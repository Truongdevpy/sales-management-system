import re

from flask import Blueprint, jsonify, request
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from models import SellerBankConfig, db, Order, OrderItem, User
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
        phone = self._normalize_phone(data.get('phone') or '')
        address = (data.get('address') or '').strip()
        business_type = (data.get('business_type') or data.get('businessType') or '').strip()
        shop_description = (data.get('shop_description') or data.get('shopDescription') or '').strip()

        if role not in ('customer', 'seller'):
            return {"status": "error", "message": "Role khong hop le"}, 400

        validation_error = self._validate_registration_rules(
            username=username,
            password=password,
            full_name=full_name,
            role=role,
            shop_name=shop_name,
            phone=phone,
            address=address,
            business_type=business_type,
            shop_description=shop_description,
        )
        if validation_error:
            return {"status": "error", "message": validation_error}, 400

        existing_user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if existing_user:
            return {"status": "error", "message": "Tai khoan da ton tai"}, 409

        if role == 'seller':
            existing_shop = User.query.filter(
                User.role == 'seller',
                func.lower(User.shop_name) == shop_name.lower(),
            ).first()
            if existing_shop:
                return {"status": "error", "message": "Ten shop da ton tai"}, 409

        seller_status = 'pending' if role == 'seller' else 'approved'
        user = User(
            username=username,
            password=generate_password_hash(password),
            full_name=full_name,
            role=role,
            seller_status=seller_status,
            shop_name=shop_name if role == 'seller' else None,
            phone=phone or None,
            address=address if role == 'seller' else None,
            business_type=business_type if role == 'seller' else None,
            shop_description=shop_description if role == 'seller' else None,
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
                    User.phone.like(search),
                    User.address.like(search),
                    User.business_type.like(search),
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
        bank_config = SellerBankConfig.query.filter_by(seller_id=seller.id).first()
        data["bankConfig"] = bank_config.to_dict() if bank_config else None
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
        phone = self._normalize_phone(data.get('phone') or '')
        address = (data.get('address') or '').strip()
        business_type = (data.get('business_type') or data.get('businessType') or '').strip()
        shop_description = (data.get('shop_description') or data.get('shopDescription') or '').strip()

        if username and username.lower() != seller.username.lower():
            if not self._is_valid_username(username):
                return {"status": "error", "message": "Username chi duoc dung 4-50 ky tu, khong co khoang trang"}, 400
            existing_user = User.query.filter(
                func.lower(User.username) == username.lower(),
                User.id != seller.id,
            ).first()
            if existing_user:
                return {"status": "error", "message": "Username da ton tai"}, 409
            seller.username = username

        if full_name:
            if len(full_name) < 4:
                return {"status": "error", "message": "Ten chu shop phai co it nhat 4 ky tu"}, 400
            seller.full_name = full_name

        if shop_name:
            if len(shop_name) < 3 or len(shop_name) > 100:
                return {"status": "error", "message": "Ten shop phai tu 3 den 100 ky tu"}, 400
            existing_shop = User.query.filter(
                User.role == 'seller',
                func.lower(User.shop_name) == shop_name.lower(),
                User.id != seller.id,
            ).first()
            if existing_shop:
                return {"status": "error", "message": "Ten shop da ton tai"}, 409
            seller.shop_name = shop_name

        if phone:
            if not self._is_valid_phone(phone):
                return {"status": "error", "message": "So dien thoai phai gom 9-11 chu so"}, 400
            seller.phone = phone

        if address:
            seller.address = address

        if business_type:
            seller.business_type = business_type

        if shop_description:
            seller.shop_description = shop_description

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

    def get_seller_bank_config(self, seller_id):
        seller = User.query.filter_by(id=seller_id, role='seller').first()
        if not seller:
            return None

        config = SellerBankConfig.query.filter_by(seller_id=seller_id).first()
        return config.to_dict() if config else {
            "sellerId": seller_id,
            "bankName": "",
            "bankAcqId": "",
            "accountNo": "",
            "accountName": "",
            "vietqrClientId": "",
            "vietqrApiKey": "",
            "bankHistoryToken": "",
            "isActive": True,
        }

    def save_seller_bank_config(self, seller_id, data):
        seller = User.query.filter_by(id=seller_id, role='seller').first()
        if not seller:
            return {"status": "error", "message": "Khong tim thay seller"}, 404

        account_no = (data.get('accountNo') or data.get('account_no') or '').strip()
        account_name = (data.get('accountName') or data.get('account_name') or '').strip()
        bank_acq_id = (data.get('bankAcqId') or data.get('bank_acq_id') or '').strip()
        if not account_no or not account_name:
            return {"status": "error", "message": "Vui long nhap so tai khoan va ten chu tai khoan"}, 400
        if not bank_acq_id:
            return {"status": "error", "message": "Vui long chon ngan hang de tao ma VietQR"}, 400

        config = SellerBankConfig.query.filter_by(seller_id=seller_id).first()
        if not config:
            config = SellerBankConfig(
                seller_id=seller_id,
                account_no=account_no,
                account_name=account_name,
            )
            self.db.session.add(config)

        config.bank_name = (data.get('bankName') or data.get('bank_name') or '').strip() or None
        config.bank_acq_id = bank_acq_id
        config.account_no = account_no
        config.account_name = account_name
        config.vietqr_client_id = (data.get('vietqrClientId') or data.get('vietqr_client_id') or '').strip() or None
        config.vietqr_api_key = (data.get('vietqrApiKey') or data.get('vietqr_api_key') or '').strip() or None
        config.bank_history_token = (data.get('bankHistoryToken') or data.get('bank_history_token') or '').strip() or None
        config.is_active = bool(data.get('isActive', data.get('is_active', True)))

        self.db.session.commit()
        return {
            "status": "success",
            "message": "Cap nhat cau hinh ngan hang thanh cong",
            "bankConfig": config.to_dict(),
        }, 200

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

    def _validate_registration_rules(
        self,
        username,
        password,
        full_name,
        role,
        shop_name,
        phone,
        address,
        business_type,
        shop_description,
    ):
        if not username or not password or not full_name:
            return "Vui long nhap day du tai khoan, mat khau va ho ten"
        if not self._is_valid_username(username):
            return "Username/email phai tu 4-50 ky tu, khong co khoang trang"
        if len(full_name) < 4:
            return "Ho ten phai co it nhat 4 ky tu"
        if len(password) < 6:
            return "Mat khau phai co it nhat 6 ky tu"
        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            return "Mat khau phai co ca chu va so"

        if role == 'seller':
            if not shop_name:
                return "Seller can nhap ten shop"
            if len(shop_name) < 3 or len(shop_name) > 100:
                return "Ten shop phai tu 3 den 100 ky tu"
            if not phone:
                return "Seller can nhap so dien thoai"
            if not self._is_valid_phone(phone):
                return "So dien thoai phai gom 9-11 chu so"
            if len(address) < 6:
                return "Seller can nhap dia chi shop ro rang"
            if len(business_type) < 2:
                return "Seller can chon/nghap nganh hang kinh doanh"
            if len(shop_description) < 10:
                return "Mo ta shop phai co it nhat 10 ky tu"

        return None

    def _is_valid_username(self, username):
        return (
            4 <= len(username) <= 50
            and bool(re.fullmatch(r"[A-Za-z0-9@._-]+", username))
        )

    def _normalize_phone(self, phone):
        return re.sub(r"[\s.\-()]+", "", str(phone or ""))

    def _is_valid_phone(self, phone):
        return bool(re.fullmatch(r"\d{9,11}", phone or ""))


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


@user_bp.route('/seller-management/<int:seller_id>/bank-config', methods=['GET'])
def api_get_seller_bank_config(seller_id):
    service = UserService(db)
    result = service.get_seller_bank_config(seller_id)
    if result is None:
        return jsonify({"message": "Khong tim thay seller"}), 404
    return jsonify(result), 200


@user_bp.route('/seller-management/<int:seller_id>/bank-config', methods=['PUT', 'PATCH'])
def api_save_seller_bank_config(seller_id):
    service = UserService(db)
    result, status_code = service.save_seller_bank_config(seller_id, request.get_json() or {})
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
