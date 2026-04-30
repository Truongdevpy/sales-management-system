from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_

from models import Customer, db


customer_bp = Blueprint('customer_bp', __name__)


class CustomerService:
    def __init__(self, db_session):
        self.db = db_session

    def get_customers(self, keyword=None, status=None):
        query = Customer.query

        if keyword:
            search = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    Customer.full_name.like(search),
                    Customer.email.like(search),
                    Customer.phone.like(search),
                    Customer.address.like(search),
                )
            )

        if status and status != 'all':
            query = query.filter(Customer.status == status)

        customers = query.order_by(Customer.created_at.desc()).all()
        return [customer.to_dict() for customer in customers]

    def get_customer(self, customer_id):
        customer = self.db.session.get(Customer, customer_id)
        return customer.to_dict() if customer else None

    def add_customer(self, data):
        try:
            error = self._validate_customer_data(data, required=True)
            if error:
                return {"status": "error", "message": error}, 400

            email = (data.get('email') or '').strip() or None
            if email and self._email_exists(email):
                return {"status": "error", "message": "Email khach hang da ton tai"}, 409

            customer = Customer(
                full_name=data.get('full_name') or data.get('fullName'),
                email=email,
                phone=data.get('phone'),
                address=data.get('address'),
                status=data.get('status') or 'active',
            )
            self.db.session.add(customer)
            self.db.session.commit()
            return {
                "status": "success",
                "message": "Them khach hang thanh cong",
                "customer": customer.to_dict(),
            }, 201
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}, 400

    def update_customer(self, customer_id, data):
        try:
            customer = self.db.session.get(Customer, customer_id)
            if not customer:
                return {"status": "error", "message": "Khong tim thay khach hang"}, 404

            error = self._validate_customer_data(data, required=False)
            if error:
                return {"status": "error", "message": error}, 400

            email = data.get('email')
            if email is not None:
                email = email.strip() or None
                if email and self._email_exists(email, exclude_id=customer.id):
                    return {"status": "error", "message": "Email khach hang da ton tai"}, 409
                customer.email = email

            full_name = data.get('full_name') or data.get('fullName')
            if full_name is not None:
                customer.full_name = full_name

            if data.get('phone') is not None:
                customer.phone = data.get('phone')

            if data.get('address') is not None:
                customer.address = data.get('address')

            if data.get('status') is not None:
                customer.status = data.get('status')

            self.db.session.commit()
            return {
                "status": "success",
                "message": "Cap nhat khach hang thanh cong",
                "customer": customer.to_dict(),
            }, 200
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}, 400

    def delete_customer(self, customer_id):
        try:
            customer = self.db.session.get(Customer, customer_id)
            if not customer:
                return {"status": "error", "message": "Khong tim thay khach hang"}, 404

            self.db.session.delete(customer)
            self.db.session.commit()
            return {"status": "success", "message": "Xoa khach hang thanh cong"}, 200
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}, 400

    def get_customer_stats(self):
        total = Customer.query.count()
        active = Customer.query.filter_by(status='active').count()
        inactive = Customer.query.filter_by(status='inactive').count()
        return {
            "total": total,
            "active": active,
            "inactive": inactive,
        }

    def _email_exists(self, email, exclude_id=None):
        query = Customer.query.filter(func.lower(Customer.email) == email.lower())
        if exclude_id:
            query = query.filter(Customer.id != exclude_id)
        return query.first() is not None

    def _validate_customer_data(self, data, required=False):
        full_name = data.get('full_name') or data.get('fullName')
        if required and not full_name:
            return "Thieu ten khach hang"

        status = data.get('status')
        if status and status not in ('active', 'inactive'):
            return "Trang thai khach hang khong hop le"

        return None


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


@customer_bp.route('/', methods=['POST'])
def api_add_customer():
    service = CustomerService(db)
    result, status_code = service.add_customer(request.get_json() or {})
    return jsonify(result), status_code


@customer_bp.route('/<int:customer_id>', methods=['PUT', 'PATCH'])
def api_update_customer(customer_id):
    service = CustomerService(db)
    result, status_code = service.update_customer(customer_id, request.get_json() or {})
    return jsonify(result), status_code


@customer_bp.route('/<int:customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    service = CustomerService(db)
    result, status_code = service.delete_customer(customer_id)
    return jsonify(result), status_code
