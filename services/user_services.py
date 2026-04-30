from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, Order, OrderItem, User
from models.product_model import Product


user_bp = Blueprint('user_bp', __name__)


class UserService:
    def __init__(self, db_session):
        self.db = db_session

    def register(self, data):
        username = (data.get('username') or data.get('email') or '').strip()
        password = data.get('password') or ''
        full_name = (data.get('full_name') or data.get('fullName') or '').strip()
        role = data.get('role') or 'customer'
        shop_name = (data.get('shop_name') or data.get('shopName') or '').strip()

        if role not in ('customer', 'seller'):
            return {"status": "error", "message": "Role khong hop le"}, 400

        if not username or not password or not full_name:
            return {"status": "error", "message": "Vui long nhap day du thong tin"}, 400

        if role == 'seller' and not shop_name:
            return {"status": "error", "message": "Seller can nhap ten shop"}, 400

        existing_user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if existing_user:
            return {"status": "error", "message": "Tai khoan da ton tai"}, 409

        seller_status = 'pending' if role == 'seller' else 'approved'
        user = User(
            username=username,
            password=generate_password_hash(password),
            full_name=full_name,
            role=role,
            seller_status=seller_status,
            shop_name=shop_name if role == 'seller' else None,
        )

        self.db.session.add(user)
        self.db.session.commit()

        message = "Dang ky thanh cong"
        if role == 'seller':
            message = "Dang ky seller thanh cong. Vui long cho admin duyet."

        return {
            "status": "success",
            "message": message,
            "requiresApproval": role == 'seller',
            "user": user.to_session_dict() if role == 'customer' else None,
        }, 201

    def login(self, data):
        username = (data.get('username') or data.get('email') or '').strip()
        password = data.get('password') or ''

        user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if not user:
            return {"status": "error", "message": "Sai tai khoan hoac mat khau"}, 401

        password_ok = False
        if user.password:
            password_ok = check_password_hash(user.password, password) if user.password.startswith('scrypt:') or user.password.startswith('pbkdf2:') else user.password == password

        if not password_ok:
            return {"status": "error", "message": "Sai tai khoan hoac mat khau"}, 401

        if user.role == 'seller':
            if user.seller_status == 'pending':
                return {"status": "error", "message": "Tai khoan seller dang cho admin duyet"}, 403
            if user.seller_status == 'rejected':
                return {"status": "error", "message": "Tai khoan seller da bi tu choi"}, 403

        return {"status": "success", "user": user.to_session_dict()}, 200

    def get_seller_requests(self):
        users = User.query.filter(User.role == 'seller').order_by(User.created_at.desc()).all()
        return [user.to_seller_review_dict() for user in users]

    def get_seller_management_list(self, status=None, keyword=None):
        query = User.query.filter(User.role == 'seller')

        if status and status != 'all':
            query = query.filter(User.seller_status == status)

        if keyword:
            search = f"%{keyword.strip()}%"
            query = query.filter(
                or_(
                    User.username.like(search),
                    User.full_name.like(search),
                    User.shop_name.like(search),
                )
            )

        sellers = query.order_by(User.created_at.desc()).all()
        return [
            seller.to_seller_management_dict(self._get_seller_management_stats(seller.id))
            for seller in sellers
        ]

    def get_seller_management_detail(self, seller_id):
        seller = User.query.filter_by(id=seller_id, role='seller').first()
        if not seller:
            return None

        data = seller.to_seller_management_dict(self._get_seller_management_stats(seller.id))
        data["products"] = [
            product.to_dict()
            for product in Product.query.filter_by(user_id=seller.id).order_by(Product.created_at.desc()).all()
        ]
        data["buyers"] = self.get_shop_buyers(seller.id)["buyers"]
        return data

    def update_seller_management(self, seller_id, data):
        seller = User.query.filter_by(id=seller_id, role='seller').first()
        if not seller:
            return {"status": "error", "message": "Khong tim thay seller"}, 404

        username = (data.get('username') or data.get('email') or '').strip()
        full_name = (data.get('full_name') or data.get('fullName') or '').strip()
        shop_name = (data.get('shop_name') or data.get('shopName') or '').strip()
        seller_status = (data.get('seller_status') or data.get('status') or '').strip()

        if username and username.lower() != seller.username.lower():
            existing_user = User.query.filter(
                func.lower(User.username) == username.lower(),
                User.id != seller.id,
            ).first()
            if existing_user:
                return {"status": "error", "message": "Username da ton tai"}, 409
            seller.username = username

        if full_name:
            seller.full_name = full_name

        if shop_name:
            seller.shop_name = shop_name

        if seller_status:
            if seller_status not in ('pending', 'approved', 'rejected'):
                return {"status": "error", "message": "Trang thai seller khong hop le"}, 400
            seller.seller_status = seller_status

        self.db.session.commit()
        return {
            "status": "success",
            "message": "Cap nhat seller thanh cong",
            "seller": seller.to_seller_management_dict(self._get_seller_management_stats(seller.id)),
        }, 200

    def update_seller_status(self, user_id, status):
        if status not in ('approved', 'rejected'):
            return False

        user = User.query.filter_by(id=user_id, role='seller').first()
        if not user:
            return False

        user.seller_status = status
        self.db.session.commit()
        return True

    def get_active_sellers(self):
        sellers = User.query.filter_by(role='seller', seller_status='approved').order_by(User.created_at.desc()).all()
        results = []
        for seller in sellers:
            total_products = Product.query.filter_by(user_id=seller.id).count()
            sales_stats = self._get_shop_sales_stats(seller.id)

            results.append({
                "id": seller.id,
                "userId": seller.id,
                "shopName": seller.shop_name or seller.full_name or seller.username,
                "joinedAt": seller.created_at.strftime("%Y-%m-%d") if seller.created_at else None,
                "totalProducts": total_products,
                "totalBuyers": sales_stats["totalBuyers"],
                "totalOrders": sales_stats["totalOrders"],
                "totalSales": sales_stats["totalSales"],
                "status": seller.seller_status,
            })
        return results

    def get_shop_buyer_statistics(self):
        sellers = User.query.filter_by(role='seller', seller_status='approved').order_by(User.created_at.desc()).all()
        results = []

        for seller in sellers:
            sales_stats = self._get_shop_sales_stats(seller.id)
            results.append({
                "sellerId": seller.id,
                "shopName": seller.shop_name or seller.full_name or seller.username,
                "ownerName": seller.full_name or seller.username,
                "totalBuyers": sales_stats["totalBuyers"],
                "totalOrders": sales_stats["totalOrders"],
                "totalSales": sales_stats["totalSales"],
            })

        return results

    def get_shop_buyers(self, seller_id):
        seller = User.query.filter_by(id=seller_id, role='seller').first()
        if not seller:
            return None

        rows = (
            self.db.session.query(
                User.id.label('buyer_id'),
                User.full_name.label('buyer_name'),
                User.username.label('buyer_username'),
                func.count(func.distinct(Order.id)).label('total_orders'),
                func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label('total_spent'),
                func.max(Order.created_at).label('last_order_at'),
            )
            .join(Order, Order.customer_id == User.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.user_id == seller_id)
            .group_by(User.id, User.full_name, User.username)
            .order_by(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).desc())
            .all()
        )

        return {
            "sellerId": seller.id,
            "shopName": seller.shop_name or seller.full_name or seller.username,
            "buyers": [
                {
                    "buyerId": row.buyer_id,
                    "buyerName": row.buyer_name or row.buyer_username,
                    "buyerUsername": row.buyer_username,
                    "totalOrders": int(row.total_orders or 0),
                    "totalSpent": float(row.total_spent or 0),
                    "lastOrderAt": row.last_order_at.strftime("%Y-%m-%d %H:%M:%S") if row.last_order_at else None,
                }
                for row in rows
            ],
        }

    def _get_shop_sales_stats(self, seller_id):
        stats = (
            self.db.session.query(
                func.count(func.distinct(Order.id)).label('total_orders'),
                func.count(func.distinct(Order.customer_id)).label('total_buyers'),
                func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label('total_sales'),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.user_id == seller_id)
            .one()
        )

        return {
            "totalOrders": int(stats.total_orders or 0),
            "totalBuyers": int(stats.total_buyers or 0),
            "totalSales": float(stats.total_sales or 0),
        }

    def _get_seller_management_stats(self, seller_id):
        sales_stats = self._get_shop_sales_stats(seller_id)
        sales_stats["totalProducts"] = Product.query.filter_by(user_id=seller_id).count()
        return sales_stats


@user_bp.route('/register', methods=['POST'])
def api_register():
    service = UserService(db)
    result, status_code = service.register(request.get_json() or {})
    return jsonify(result), status_code


@user_bp.route('/login', methods=['POST'])
def api_login():
    service = UserService(db)
    result, status_code = service.login(request.get_json() or {})
    return jsonify(result), status_code


@user_bp.route('/seller-requests', methods=['GET'])
def api_get_seller_requests():
    service = UserService(db)
    return jsonify(service.get_seller_requests()), 200


@user_bp.route('/seller-management', methods=['GET'])
def api_get_seller_management_list():
    service = UserService(db)
    status = request.args.get('status', 'all')
    keyword = request.args.get('keyword', '')
    return jsonify(service.get_seller_management_list(status=status, keyword=keyword)), 200


@user_bp.route('/seller-management/<int:seller_id>', methods=['GET'])
def api_get_seller_management_detail(seller_id):
    service = UserService(db)
    result = service.get_seller_management_detail(seller_id)
    if result is None:
        return jsonify({"message": "Khong tim thay seller"}), 404
    return jsonify(result), 200


@user_bp.route('/seller-management/<int:seller_id>', methods=['PUT', 'PATCH'])
def api_update_seller_management(seller_id):
    service = UserService(db)
    result, status_code = service.update_seller_management(seller_id, request.get_json() or {})
    return jsonify(result), status_code


@user_bp.route('/sellers', methods=['GET'])
def api_get_active_sellers():
    service = UserService(db)
    return jsonify(service.get_active_sellers()), 200


@user_bp.route('/seller-buyer-stats', methods=['GET'])
def api_get_shop_buyer_statistics():
    service = UserService(db)
    return jsonify(service.get_shop_buyer_statistics()), 200


@user_bp.route('/sellers/<int:seller_id>/buyers', methods=['GET'])
def api_get_shop_buyers(seller_id):
    service = UserService(db)
    result = service.get_shop_buyers(seller_id)
    if result is None:
        return jsonify({"message": "Khong tim thay shop"}), 404
    return jsonify(result), 200


@user_bp.route('/seller-requests/<int:user_id>/<status>', methods=['POST'])
def api_update_seller_status(user_id, status):
    service = UserService(db)
    if service.update_seller_status(user_id, status):
        return jsonify({"message": "Cap nhat trang thai seller thanh cong"}), 200
    return jsonify({"message": "Khong tim thay seller hoac trang thai khong hop le"}), 404
