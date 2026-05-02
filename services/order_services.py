from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem
from models.product_model import Product
from decimal import Decimal, InvalidOperation

class OrderService:
    def __init__(self, db_session):
        # db_session là db.session từ Flask-SQLAlchemy[cite: 8]
        self.db = db_session

    def place_order(self, customer_id, cart_data):
        """
        Xử lý đặt hàng: Kiểm tra tồn kho, tính toán bằng Decimal và trừ kho.[cite: 8]
        """
        try:
            # Kiểm tra dữ liệu đầu vào cơ bản
            if not customer_id or not cart_data or not isinstance(cart_data, list):
                return {"status": "error", "message": "Dữ liệu khách hàng hoặc giỏ hàng không hợp lệ"}, 400

            # 1. Khởi tạo đơn hàng nháp
            new_order = Order(
                customer_id=customer_id,
                total_amount=0,
                payment_status='chờ thanh toán'
            )
            self.db.add(new_order)
            self.db.flush() # Lấy ID để dùng cho OrderItem[cite: 8]

            total_bill = Decimal('0.00')

            # 2. Duyệt qua từng sản phẩm trong giỏ hàng
            for item in cart_data:
                p_id = item.get('product_id')
                qty = item.get('quantity')

                if p_id is None or qty is None:
                    raise Exception("Thiếu thông tin sản phẩm hoặc số lượng trong giỏ hàng")

                # Truy vấn sản phẩm
                product = self.db.get(Product, p_id)
                if not product:
                    raise Exception(f"Sản phẩm ID {p_id} không tồn tại")
                
                try:
                    qty_to_buy = int(qty)
                    if qty_to_buy <= 0:
                        raise Exception(f"Số lượng mua của {product.name} phải lớn hơn 0")
                except ValueError:
                    raise Exception(f"Số lượng của sản phẩm {product.name} không phải là số hợp lệ")
                
                # KIỂM TRA TỒN KHO[cite: 8]
                if product.quantity < qty_to_buy:
                    raise Exception(f"Sản phẩm '{product.name}' không đủ hàng (Còn: {product.quantity})")

                # Tính toán tiền tệ chính xác[cite: 8]
                try:
                    item_price = Decimal(str(product.price))
                except InvalidOperation:
                    raise Exception(f"Giá sản phẩm {product.name} không hợp lệ")

                subtotal = item_price * qty_to_buy
                total_bill += subtotal

                # Tạo chi tiết đơn hàng
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=qty_to_buy,
                    price=item_price
                )
                
                # CẬP NHẬT TỒN KHO[cite: 8]
                product.quantity -= qty_to_buy
                self.db.add(order_item)

            # 3. Hoàn tất đơn hàng
            new_order.total_amount = total_bill
            self.db.commit()
            
            return {
                "status": "success", 
                "order_id": new_order.id, 
                "total": float(total_bill)
            }, 201

        except Exception as e:
            self.db.rollback() # Trả lại trạng thái cũ nếu có lỗi[cite: 8]
            return {"status": "error", "message": str(e)}, 400

    def confirm_payment(self, order_id):
        order = self.db.get(Order, order_id)
        if order:
            order.payment_status = 'đã thanh toán'
            self.db.commit()
            return True
        return False

    def get_user_orders(self, customer_id):
        orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).all()
        return [{
            "id": o.id,
            "total_amount": float(o.total_amount),
            "shipping_status": o.shipping_status,
            "payment_status": o.payment_status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else None
        } for o in orders]

    def get_order_details(self, order_id):
        order = self.db.get(Order, order_id)
        if not order:
            return None
        
        return {
            "id": order.id,
            "total_amount": float(order.total_amount),
            "shipping_status": order.shipping_status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
            "items": [{
                "product_name": item.product.name if item.product else f"Sản phẩm #{item.product_id}",
                "quantity": item.quantity,
                "price": float(item.price),
                "subtotal": float(item.price * item.quantity)
            } for item in order.items]
        }
    
    def get_seller_orders(self, seller_id):
        """Lấy tất cả đơn hàng có chứa sản phẩm của Seller này"""
        # Join các bảng để lọc đơn hàng theo người bán
        orders = (
            self.db.session.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.user_id == seller_id)
            .distinct()
            .order_by(Order.created_at.desc())
            .all()
        )
        return [{
            "id": o.id,
            "total_amount": float(o.total_amount),
            "shipping_status": o.shipping_status,
            "payment_status": o.payment_status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for o in orders]

    def update_order_status(self, order_id, shipping_status, payment_status):
        """Cập nhật trạng thái vận chuyển và thanh toán[cite: 8, 11]"""
        order = self.db.get(Order, order_id)
        if not order:
            return False
        
        if shipping_status:
            order.shipping_status = shipping_status
        if payment_status:
            order.payment_status = payment_status
            
        self.db.commit()
        return True

# --- CẤU HÌNH API ROUTES ---
order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/place-order', methods=['POST'])
def api_place_order():
    data = request.get_json() or {}
    service = OrderService(db.session)
    # Trả về kết quả trực tiếp từ service[cite: 8]
    result, status_code = service.place_order(data.get('customer_id'), data.get('cart_data'))
    return jsonify(result), status_code

@order_bp.route('/my-orders/<int:customer_id>', methods=['GET'])
def api_get_my_orders(customer_id):
    service = OrderService(db.session)
    return jsonify(service.get_user_orders(customer_id)), 200

@order_bp.route('/<int:order_id>', methods=['GET'])
def api_get_order_detail(order_id):
    service = OrderService(db.session)
    result = service.get_order_details(order_id)
    if not result:
        return jsonify({"message": "Không tìm thấy đơn hàng"}), 404
    return jsonify(result), 200

@order_bp.route('/confirm-payment/<int:order_id>', methods=['POST'])
def api_confirm_payment(order_id):
    service = OrderService(db.session)
    if service.confirm_payment(order_id):
        return jsonify({"message": "Thanh toán thành công"}), 200
    return jsonify({"message": "Không tìm thấy đơn hàng hoặc cập nhật thất bại"}), 404


@order_bp.route('/seller/<int:seller_id>', methods=['GET'])
def api_get_seller_orders(seller_id):
    service = OrderService(db.session)
    return jsonify(service.get_seller_orders(seller_id)), 200

@order_bp.route('/update-status/<int:order_id>', methods=['PUT'])
def api_update_order_status(order_id):
    data = request.get_json()
    service = OrderService(db.session)
    success = service.update_order_status(
        order_id, 
        data.get('shipping_status'), 
        data.get('payment_status')
    )
    if success:
        return jsonify({"message": "Cập nhật thành công"}), 200
    return jsonify({"message": "Không tìm thấy đơn hàng"}), 404

