from . import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    shipping_status = db.Column(db.Enum('chờ giao', 'đang giao', 'đã giao'), default='chờ giao')
    payment_status = db.Column(db.Enum('chờ thanh toán', 'đã thanh toán', 'thất bại'), default='chờ thanh toán')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Hàm khởi tạo (Constructor)
    def __init__(self, customer_id, total_amount=0.00, payment_status='chờ thanh toán'):
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.payment_status = payment_status
        # created_at và shipping_status thường để mặc định nên không nhất thiết phải đưa vào init

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(15, 2), nullable=False)

    # Hàm khởi tạo cho chi tiết từng món hàng
    def __init__(self, product_id, quantity, price, order_id=None):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        if order_id:
            self.order_id = order_id