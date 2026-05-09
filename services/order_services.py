from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem
from models.product_model import Product
from decimal import Decimal, InvalidOperation

class OrderService:
    def __init__(self, db_session):
        self.db = db_session

    def place_order(self, customer_id, cart_data):
        try:
            if not customer_id or not cart_data or not isinstance(cart_data, list):
                return {"status": "error", "message": "Dữ liệu không hợp lệ"}, 400

            new_order = Order(customer_id=customer_id, total_amount=0, payment_status='chờ thanh toán')
            self.db.add(new_order)
            self.db.flush() 

            total_bill = Decimal('0.00')
            for item in cart_data:
                product = self.db.get(Product, item.get('product_id'))
                if not product or product.quantity < int(item.get('quantity')):
                    raise Exception(f"Sản phẩm {product.name if product else ''} không đủ hàng")

                subtotal = Decimal(str(product.price)) * int(item.get('quantity'))
                total_bill += subtotal

                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=int(item.get('quantity')),
                    price=product.price
                )
                product.quantity -= int(item.get('quantity'))
                self.db.add(order_item)

            new_order.total_amount = total_bill
            self.db.commit()
            return {"status": "success", "order_id": new_order.id, "total": float(total_bill)}, 201
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}, 400

    def get_user_orders(self, customer_id):
        orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).all()
        return [{
            "id": o.id,
            "total_amount": float(o.total_amount),
            "shipping_status": o.shipping_status,
            "payment_status": o.payment_status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for o in orders]

    def get_order_details(self, order_id):
        order = self.db.get(Order, order_id)
        if not order: return None
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "total_amount": float(order.total_amount),
            "shipping_status": order.shipping_status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [{
                "product_name": item.product.name if item.product else f"SP #{item.product_id}",
                "quantity": item.quantity,
                "price": float(item.price),
                "subtotal": float(item.price * item.quantity)
            } for item in order.items]
        }
    
    # QUAN TRỌNG: Hàm này phải nằm trong Class OrderService
    def get_seller_orders(self, seller_id):
        orders = (
            self.db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.user_id == seller_id)
            .distinct().order_by(Order.created_at.desc()).all()
        )
        return [{
            "id": o.id,
            "total_amount": float(o.total_amount),
            "shipping_status": o.shipping_status,
            "payment_status": o.payment_status,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for o in orders]

    def update_order_status(self, order_id, shipping_status=None, payment_status=None):
        """Cập nhật trạng thái vận chuyển và thanh toán"""
        order = self.db.get(Order, order_id)
        if not order:
            return False
        
        # LOGIC: Chỉ cho phép chuyển sang 'đã giao' nếu đã thanh toán thành công
        if shipping_status == 'đã giao':
            if order.payment_status != 'đã thanh toán':
                # Trả về False để thông báo lỗi logic cho Frontend
                return False 
            order.shipping_status = shipping_status
        elif shipping_status:
            order.shipping_status = shipping_status
            
        if payment_status:
            order.payment_status = payment_status
            
        self.db.commit()
        return True

# --- API ROUTES ---
order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/my-orders/<int:customer_id>', methods=['GET'])
def api_get_my_orders(customer_id):
    service = OrderService(db.session)
    return jsonify(service.get_user_orders(customer_id)), 200

@order_bp.route('/seller/<int:seller_id>', methods=['GET'])
def api_get_seller_orders(seller_id):
    service = OrderService(db.session)
    # Bây giờ gọi hàm này sẽ không còn lỗi nữa vì nó đã nằm trong class
    return jsonify(service.get_seller_orders(seller_id)), 200

@order_bp.route('/<int:order_id>', methods=['GET'])
def api_get_order_detail(order_id):
    service = OrderService(db.session)
    result = service.get_order_details(order_id)
    return jsonify(result) if result else (jsonify({"message": "Not found"}), 404)

@order_bp.route('/update-status/<int:order_id>', methods=['PUT'])
def api_update_order_status(order_id):
    service = OrderService(db.session)
    data = request.get_json()
    if service.update_order_status(order_id, data.get('shipping_status'), data.get('payment_status')):
        return jsonify({"message": "Cập nhật thành công"}), 200
    return jsonify({"message": "Không tìm thấy"}), 404