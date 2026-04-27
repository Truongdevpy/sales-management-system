from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem

class OrderService:
    def __init__(self, db_session):
        self.db = db_session

    def place_order(self, customer_id, cart_data):
        try:
            new_order = Order(
                customer_id=customer_id,
                total_amount=0,
                payment_status='chờ thanh toán'
            )
            self.db.add(new_order)
            self.db.flush() 

            final_total = 0
            for item in cart_data:
                subtotal = item['price'] * item['quantity']
                final_total += subtotal
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                self.db.add(order_item)

            new_order.total_amount = final_total
            self.db.commit()
            return {"status": "success", "order_id": new_order.id, "total": float(final_total)}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def confirm_payment(self, order_id):
        # Sử dụng session.get để tương thích với SQLAlchemy 2.0
        order = self.db.get(Order, order_id)
        if order:
            order.payment_status = 'đã thanh toán'
            self.db.commit()
            return True
        return False

order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/place-order', methods=['POST'])
def api_place_order():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Thiếu dữ liệu JSON"}), 400
        
    service = OrderService(db.session)
    result = service.place_order(data.get('customer_id'), data.get('cart_data'))

    if result['status'] == 'success':
        return jsonify(result), 201
    return jsonify(result), 400

@order_bp.route('/confirm-payment/<int:order_id>', methods=['POST'])
def api_confirm_payment(order_id):
    service = OrderService(db.session)
    if service.confirm_payment(order_id):
        return jsonify({"message": "Thanh toán thành công"}), 200
    return jsonify({"message": "Không tìm thấy đơn hàng"}), 404