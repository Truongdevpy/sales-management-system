import re

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash

from models import Order, OrderItem, User, db


customer_bp = Blueprint('customer_bp', __name__)


def require_admin_session():
    current_user = session.get('user')
    if not current_user:
        return jsonify({"message": "Vui long dang nhap"}), 401
    if current_user.get('role') != 'admin':
        return jsonify({"message": "Khong co quyen admin"}), 403
    return None


class CustomerService:
    def __init__(self, db_session):
        self.db = db_session

    def get_customers(self, keyword=None, status=None):
        total_orders = func.count(func.distinct(Order.id))
        total_products = func.coalesce(func.sum(OrderItem.quantity), 0)
        total_spent = func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0)
        last_order_at = func.max(Order.created_at)

        query = (
            self.db.session.query(
                User.id,
                User.full_name,
                User.username,
                User.role,
                User.phone,
                User.address,
                User.created_at,
                total_orders.label('total_orders'),
                total_products.label('total_products'),
                total_spent.label('total_spent'),
                last_order_at.label('last_order_at'),
            )
            .outerjoin(Order, Order.customer_id == User.id)
            .outerjoin(OrderItem, OrderItem.order_id == Order.id)
            .filter(User.role == 'customer')
            .group_by(User.id, User.full_name, User.username, User.role, User.phone, User.address, User.created_at)
        )

        if keyword:
            search = f"%{keyword.strip()}%"
            query = query.filter(or_(User.full_name.like(search), User.username.like(search), User.phone.like(search), User.address.like(search)))

        if status and status != 'all':
            if status == 'active':
                query = query.having(total_orders > 0)
            elif status == 'inactive':
                query = query.having(total_orders == 0)

        rows = query.order_by(User.created_at.desc()).all()
        return [self._customer_user_row_to_dict(row) for row in rows]

    def get_customer(self, customer_id):
        rows = self.get_customers()
        return next((customer for customer in rows if customer["id"] == customer_id), None)

    def get_customer_management_list(self, keyword=None, status=None):
        return self.get_customers(keyword=keyword, status=status)

    def get_customer_management_detail(self, customer_id):
        return self.get_customer(customer_id)

    def update_customer_management(self, customer_id, data):
        customer = User.query.filter_by(id=customer_id, role='customer').first()
        if not customer:
            return {"status": "error", "message": "Khong tim thay customer"}, 404

        username = (data.get('username') or data.get('email') or '').strip()
        full_name = (data.get('full_name') or data.get('fullName') or '').strip()
        phone = self._normalize_phone(data.get('phone') or '')
        address = (data.get('address') or '').strip()
        password = data.get('password') or ''

        if username and username.lower() != customer.username.lower():
            if not self._is_valid_username(username):
                return {"status": "error", "message": "Username/email phai tu 4-50 ky tu, khong co khoang trang"}, 400
            existing_user = User.query.filter(
                func.lower(User.username) == username.lower(),
                User.id != customer.id,
            ).first()
            if existing_user:
                return {"status": "error", "message": "Username da ton tai"}, 409
            customer.username = username

        if full_name:
            if len(full_name) < 4:
                return {"status": "error", "message": "Ho ten phai co it nhat 4 ky tu"}, 400
            customer.full_name = full_name

        if phone:
            if not self._is_valid_phone(phone):
                return {"status": "error", "message": "So dien thoai phai gom 9-11 chu so"}, 400
            customer.phone = phone
        elif 'phone' in data:
            customer.phone = None

        if 'address' in data:
            customer.address = address or None

        if password:
            if len(password) < 6 or not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
                return {"status": "error", "message": "Mat khau moi phai co it nhat 6 ky tu, gom ca chu va so"}, 400
            customer.password = generate_password_hash(password)

        self.db.session.commit()
        return {
            "status": "success",
            "message": "Cap nhat customer thanh cong",
            "customer": self.get_customer_management_detail(customer.id),
        }, 200

    def delete_customer_management(self, customer_id):
        customer = User.query.filter_by(id=customer_id, role='customer').first()
        if not customer:
            return {"status": "error", "message": "Khong tim thay customer"}, 404

        self.db.session.delete(customer)
        self.db.session.commit()
        return {"status": "success", "message": "Da xoa customer"}, 200

    def get_customer_stats(self):
        customers = self.get_customers()
        active = len([customer for customer in customers if customer["totalOrders"] > 0])
        total = len(customers)
        total_spent = sum(customer["totalSpent"] for customer in customers)
        total_products = sum(customer["totalProducts"] for customer in customers)
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "totalSpent": total_spent,
            "totalProducts": total_products,
        }

    def _customer_user_row_to_dict(self, row):
        total_orders = int(row.total_orders or 0)
        total_products = int(row.total_products or 0)
        total_spent = float(row.total_spent or 0)
        display_name = row.full_name or row.username

        return {
            "id": row.id,
            "fullName": display_name,
            "email": row.username,
            "username": row.username,
            "role": row.role,
            "phone": row.phone,
            "address": row.address,
            "status": "active" if total_orders > 0 else "inactive",
            "createdAt": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "totalSpent": total_spent,
            "lastOrderAt": row.last_order_at.strftime("%Y-%m-%d %H:%M:%S") if row.last_order_at else None,
        }

    def _is_valid_username(self, username):
        return (
            4 <= len(username) <= 50
            and bool(re.fullmatch(r"[A-Za-z0-9@._-]+", username))
        )

    def _normalize_phone(self, phone):
        return re.sub(r"[\s.\-()]+", "", str(phone or ""))

    def _is_valid_phone(self, phone):
        return bool(re.fullmatch(r"\d{9,11}", phone or ""))


@customer_bp.route('/', methods=['GET'])
def api_get_customers():
    service = CustomerService(db)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', 'all')
    return jsonify(service.get_customers(keyword=keyword, status=status)), 200


@customer_bp.route('/stats', methods=['GET'])
def api_get_customer_stats():
    service = CustomerService(db)
    return jsonify(service.get_customer_stats()), 200


@customer_bp.route('/management', methods=['GET'])
def api_get_customer_management_list():
    auth_error = require_admin_session()
    if auth_error:
        return auth_error

    service = CustomerService(db)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', 'all')
    return jsonify(service.get_customer_management_list(keyword=keyword, status=status)), 200


@customer_bp.route('/management/<int:customer_id>', methods=['GET'])
def api_get_customer_management_detail(customer_id):
    auth_error = require_admin_session()
    if auth_error:
        return auth_error

    service = CustomerService(db)
    customer = service.get_customer_management_detail(customer_id)
    if not customer:
        return jsonify({"message": "Khong tim thay customer"}), 404
    return jsonify(customer), 200


@customer_bp.route('/management/<int:customer_id>', methods=['PUT', 'PATCH'])
def api_update_customer_management(customer_id):
    auth_error = require_admin_session()
    if auth_error:
        return auth_error

    service = CustomerService(db)
    result, status_code = service.update_customer_management(customer_id, request.get_json() or {})
    return jsonify(result), status_code


@customer_bp.route('/management/<int:customer_id>', methods=['DELETE'])
def api_delete_customer_management(customer_id):
    auth_error = require_admin_session()
    if auth_error:
        return auth_error

    service = CustomerService(db)
    result, status_code = service.delete_customer_management(customer_id)
    return jsonify(result), status_code


@customer_bp.route('/<int:customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    service = CustomerService(db)
    customer = service.get_customer(customer_id)
    if not customer:
        return jsonify({"message": "Khong tim thay khach hang"}), 404
    return jsonify(customer), 200
