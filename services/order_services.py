import json
import re
from datetime import datetime
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, request

from models import Order, OrderItem, Payment, SellerBankConfig, db
from models.product_model import Product


PENDING_PAYMENT = 'chờ thanh toán'
PAID_PAYMENT = 'đã thanh toán'
FAILED_PAYMENT = 'thất bại'
DEFAULT_SHIPPING_FEE = Decimal('5000')


class OrderService:
    def __init__(self, db_session):
        self.db = db_session

    def place_order(self, customer_id, cart_data, payment_method='cod', shipping_fee=DEFAULT_SHIPPING_FEE):
        try:
            if not customer_id or not cart_data or not isinstance(cart_data, list):
                return {"status": "error", "message": "Du lieu don hang khong hop le"}, 400

            payment_method = payment_method if payment_method in ('cod', 'bank_transfer') else 'cod'
            shipping_fee = Decimal(str(shipping_fee or 0))
            cart_lines, product_total, seller_ids = self._validate_cart(cart_data)

            if payment_method == 'bank_transfer' and len(seller_ids) != 1:
                return {
                    "status": "error",
                    "message": "Thanh toan QR chi ho tro gio hang cua 1 shop. Vui long tach don hoac chon COD.",
                }, 400

            total_bill = product_total + shipping_fee
            new_order = Order(customer_id=customer_id, total_amount=total_bill, payment_status=PENDING_PAYMENT)
            self.db.add(new_order)
            self.db.flush()

            for line in cart_lines:
                product = line["product"]
                quantity = line["quantity"]
                self.db.add(OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price,
                ))
                product.quantity -= quantity

            payment = self._create_payment_for_order(new_order, payment_method, seller_ids)
            self.db.add(payment)
            self.db.commit()

            return {
                "status": "success",
                "order_id": new_order.id,
                "total": float(total_bill),
                "payment": payment.to_dict(),
                "message": "Dat hang thanh cong",
            }, 201
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}, 400

    def get_user_orders(self, customer_id):
        orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).all()
        return [self._order_summary_to_dict(order) for order in orders]

    def get_order_details(self, order_id):
        order = self.db.get(Order, order_id)
        if not order:
            return None

        payment = Payment.query.filter_by(order_id=order.id).first()
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "total_amount": float(order.total_amount),
            "shipping_status": order.shipping_status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "payment": payment.to_dict() if payment else None,
            "items": [{
                "product_name": item.product.name if item.product else f"SP #{item.product_id}",
                "seller_id": item.product.user_id if item.product else None,
                "quantity": item.quantity,
                "price": float(item.price),
                "subtotal": float(item.price * item.quantity),
            } for item in order.items],
        }

    def get_seller_orders(self, seller_id):
        orders = (
            self.db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.user_id == seller_id)
            .distinct().order_by(Order.created_at.desc()).all()
        )
        return [self._order_summary_to_dict(order) for order in orders]

    def update_order_status(self, order_id, shipping_status=None, payment_status=None):
        order = self.db.get(Order, order_id)
        if not order:
            return False

        if shipping_status == 'đã giao' and order.payment_status != PAID_PAYMENT:
            return False
        if shipping_status:
            order.shipping_status = shipping_status
        if payment_status:
            order.payment_status = payment_status

        self.db.commit()
        return True

    def create_or_get_bank_payment(self, order_id):
        order = self.db.get(Order, order_id)
        if not order:
            return {"status": "error", "message": "Khong tim thay don hang"}, 404

        payment = Payment.query.filter_by(order_id=order.id).first()
        if payment and payment.method == 'bank_transfer':
            if payment.status != 'paid':
                seller_ids = self._get_order_seller_ids(order)
                if len(seller_ids) != 1:
                    return {
                        "status": "error",
                        "message": "Thanh toan QR chi ho tro don hang cua 1 shop",
                    }, 400
                self._refresh_bank_payment(payment, order, seller_ids)
                self.db.commit()
            return {"status": "success", "payment": payment.to_dict()}, 200
        if payment and payment.status == 'paid':
            return {"status": "success", "payment": payment.to_dict()}, 200

        seller_ids = self._get_order_seller_ids(order)
        if len(seller_ids) != 1:
            return {
                "status": "error",
                "message": "Thanh toan QR chi ho tro don hang cua 1 shop",
            }, 400

        if payment:
            self.db.delete(payment)
            self.db.flush()

        payment = self._create_payment_for_order(order, 'bank_transfer', seller_ids)
        self.db.add(payment)
        self.db.commit()
        return {"status": "success", "payment": payment.to_dict()}, 200

    def get_order_payment(self, order_id):
        payment = Payment.query.filter_by(order_id=order_id).first()
        return payment.to_dict() if payment else None

    def confirm_bank_payment(self, order_id):
        order = self.db.get(Order, order_id)
        if not order:
            return {"status": "error", "message": "Khong tim thay don hang"}, 404

        payment = Payment.query.filter_by(order_id=order.id).first()
        if not payment:
            return {"status": "error", "message": "Don hang chua co thong tin thanh toan"}, 404
        if payment.status == 'paid':
            return {"status": "success", "message": "Don hang da thanh toan", "payment": payment.to_dict()}, 200
        if payment.method != 'bank_transfer':
            return {"status": "error", "message": "Don hang nay khong phai thanh toan chuyen khoan"}, 400

        config = SellerBankConfig.query.filter_by(seller_id=payment.seller_id, is_active=True).first()
        if not config or not config.bank_history_token:
            return {"status": "error", "message": "Shop chua cau hinh token ra soat giao dich"}, 400

        try:
            transactions = self._fetch_bank_transactions(config.bank_history_token)
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "payment": payment.to_dict(),
            }, 502

        matched = self._find_matching_transaction(transactions, payment)
        if not matched:
            return {
                "status": "pending",
                "message": "Ban chua chuyen khoan hoac giao dich chua khop dung so tien va noi dung chuyen khoan",
                "payment": payment.to_dict(),
            }, 200

        payment.status = 'paid'
        payment.matched_transaction_id = str(matched.get('transactionID') or '')
        payment.matched_description = matched.get('description')
        payment.paid_at = datetime.now()
        order.payment_status = PAID_PAYMENT
        self.db.commit()

        return {
            "status": "success",
            "message": "Thanh toan thanh cong",
            "payment": payment.to_dict(),
        }, 200

    def _validate_cart(self, cart_data):
        cart_lines = []
        seller_ids = set()
        product_total = Decimal('0')

        for item in cart_data:
            product_id = item.get('product_id')
            quantity = int(item.get('quantity') or 0)
            if quantity <= 0:
                raise Exception("So luong san pham khong hop le")

            product = self.db.get(Product, product_id)
            if not product:
                raise Exception("Khong tim thay san pham")
            if product.quantity is None or product.quantity < quantity:
                raise Exception(f"San pham {product.name} khong du hang")

            cart_lines.append({"product": product, "quantity": quantity})
            seller_ids.add(product.user_id)
            product_total += Decimal(str(product.price)) * quantity

        return cart_lines, product_total, seller_ids

    def _create_payment_for_order(self, order, method, seller_ids):
        seller_id = next(iter(seller_ids)) if len(seller_ids) == 1 else None
        payment = Payment(
            order_id=order.id,
            seller_id=seller_id,
            method=method,
            amount=order.total_amount,
            status='pending',
            payment_code=f"COD{order.id}" if method == 'cod' else f"ORD{order.id}S{seller_id}",
            qr_content=None,
        )

        if method == 'bank_transfer':
            self._apply_current_bank_config(payment, seller_id)

        return payment

    def _refresh_bank_payment(self, payment, order, seller_ids):
        seller_id = next(iter(seller_ids))
        payment.seller_id = seller_id
        payment.amount = order.total_amount
        payment.payment_code = payment.payment_code or f"ORD{order.id}S{seller_id}"
        if not payment.payment_code.endswith(f"S{seller_id}"):
            payment.payment_code = f"ORD{order.id}S{seller_id}"
        payment.qr_content = payment.payment_code
        self._apply_current_bank_config(payment, seller_id)

    def _apply_current_bank_config(self, payment, seller_id):
        config = SellerBankConfig.query.filter_by(seller_id=seller_id, is_active=True).first()
        if not config:
            raise Exception("Shop chua cau hinh ngan hang. Vui long chon COD hoac lien he shop.")
        payment.qr_content = payment.payment_code
        payment.qr_data_url = self._generate_vietqr(config, payment)
        return config

    def _generate_vietqr(self, config, payment):
        if not config.bank_acq_id:
            raise Exception("Shop chua cau hinh Bank ACQ ID de tao QR VietQR")

        content = payment.payment_code
        amount = int(Decimal(str(payment.amount)))
        fallback = (
            f"https://img.vietqr.io/image/{config.bank_acq_id}-{config.account_no}-compact.png"
            f"?amount={amount}&addInfo={quote(content)}&accountName={quote(config.account_name)}"
        )

        return fallback

    def _fetch_bank_transactions(self, token):
        token = str(token or '').strip()
        if not token:
            raise Exception("Shop chua cau hinh token ra soat giao dich")

        url = f"https://thueapi.pro/historyapimbbankv2/{quote(token, safe='')}"
        req = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "SalesManagementSystem/1.0",
            },
            method="GET",
        )
        try:
            with urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            raise Exception(f"API lich su ngan hang loi HTTP {exc.code}: {body[:160] or exc.reason}")
        except (URLError, TimeoutError) as exc:
            raise Exception(f"Khong the ket noi API lich su ngan hang: {exc}")
        except ValueError:
            raise Exception("API lich su ngan hang tra ve du lieu khong dung JSON")

        transactions = result.get("transactions")
        if transactions is None:
            message = result.get("message") or result.get("msg") or "API khong tra ve danh sach giao dich"
            raise Exception(message)
        if not isinstance(transactions, list):
            raise Exception("Danh sach giao dich khong hop le")

        return transactions

    def _find_matching_transaction(self, transactions, payment):
        code = self._normalize_transfer_text(payment.payment_code or '')
        amount = self._parse_money(payment.amount)
        for transaction in transactions:
            tran_type = str(transaction.get('type') or '').upper()
            description = self._normalize_transfer_text(transaction.get('description') or '')
            tran_amount = self._parse_money(transaction.get('amount') or 0)

            if tran_type == 'IN' and tran_amount == amount and code and code in description:
                return transaction
        return None

    def _normalize_transfer_text(self, value):
        return re.sub(r"\s+", "", str(value or "").lower())

    def _parse_money(self, value):
        try:
            cleaned = str(value or 0).replace(",", "").replace(" ", "")
            return int(Decimal(cleaned))
        except Exception:
            return 0

    def _get_order_seller_ids(self, order):
        return {item.product.user_id for item in order.items if item.product}

    def _order_summary_to_dict(self, order):
        payment = Payment.query.filter_by(order_id=order.id).first()
        return {
            "id": order.id,
            "total_amount": float(order.total_amount),
            "shipping_status": order.shipping_status,
            "payment_status": order.payment_status,
            "payment_method": payment.method if payment else None,
            "payment": payment.to_dict() if payment else None,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


order_bp = Blueprint('order_bp', __name__)


@order_bp.route('/place-order', methods=['POST'])
def api_place_order():
    service = OrderService(db.session)
    data = request.get_json() or {}
    result, status_code = service.place_order(
        customer_id=data.get('customer_id'),
        cart_data=data.get('cart_data'),
        payment_method=data.get('payment_method', 'cod'),
        shipping_fee=data.get('shipping_fee', DEFAULT_SHIPPING_FEE),
    )
    return jsonify(result), status_code


@order_bp.route('/my-orders/<int:customer_id>', methods=['GET'])
def api_get_my_orders(customer_id):
    service = OrderService(db.session)
    return jsonify(service.get_user_orders(customer_id)), 200


@order_bp.route('/seller/<int:seller_id>', methods=['GET'])
def api_get_seller_orders(seller_id):
    service = OrderService(db.session)
    return jsonify(service.get_seller_orders(seller_id)), 200


@order_bp.route('/<int:order_id>', methods=['GET'])
def api_get_order_detail(order_id):
    service = OrderService(db.session)
    result = service.get_order_details(order_id)
    return jsonify(result) if result else (jsonify({"message": "Not found"}), 404)


@order_bp.route('/<int:order_id>/payment', methods=['GET'])
def api_get_order_payment(order_id):
    service = OrderService(db.session)
    result = service.get_order_payment(order_id)
    return jsonify(result) if result else (jsonify({"message": "Payment not found"}), 404)


@order_bp.route('/<int:order_id>/payment', methods=['POST'])
def api_create_order_payment(order_id):
    service = OrderService(db.session)
    result, status_code = service.create_or_get_bank_payment(order_id)
    return jsonify(result), status_code


@order_bp.route('/confirm-payment/<int:order_id>', methods=['POST'])
def api_confirm_payment(order_id):
    service = OrderService(db.session)
    result, status_code = service.confirm_bank_payment(order_id)
    return jsonify(result), status_code


@order_bp.route('/update-status/<int:order_id>', methods=['PUT'])
def api_update_order_status(order_id):
    service = OrderService(db.session)
    data = request.get_json() or {}
    if service.update_order_status(order_id, data.get('shipping_status'), data.get('payment_status')):
        return jsonify({"message": "Cap nhat thanh cong"}), 200
    return jsonify({"message": "Khong tim thay hoac trang thai khong hop le"}), 404
