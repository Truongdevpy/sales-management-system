from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from models import Order, OrderItem, User, db


customer_bp = Blueprint('customer_bp', __name__)


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
                User.created_at,
                total_orders.label('total_orders'),
                total_products.label('total_products'),
                total_spent.label('total_spent'),
                last_order_at.label('last_order_at'),
            )
            .outerjoin(Order, Order.customer_id == User.id)
            .outerjoin(OrderItem, OrderItem.order_id == Order.id)
            .filter(User.role == 'customer')
            .group_by(User.id, User.full_name, User.username, User.created_at)
        )

        if keyword:
            search = f"%{keyword.strip()}%"
            query = query.filter(or_(User.full_name.like(search), User.username.like(search)))

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
            "status": "active" if total_orders > 0 else "inactive",
            "createdAt": row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else None,
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "totalSpent": total_spent,
            "lastOrderAt": row.last_order_at.strftime("%Y-%m-%d %H:%M:%S") if row.last_order_at else None,
        }


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


@customer_bp.route('/<int:customer_id>', methods=['GET'])
def api_get_customer(customer_id):
    service = CustomerService(db)
    customer = service.get_customer(customer_id)
    if not customer:
        return jsonify({"message": "Khong tim thay khach hang"}), 404
    return jsonify(customer), 200
