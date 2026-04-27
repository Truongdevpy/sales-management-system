from . import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    # Lưu ý: Đảm bảo bạn đã có bảng 'users' trước khi chạy
    customer_id = db.Column(db.Integer, nullable=False) 
    total_amount = db.Column(db.Numeric(15, 2), default=0.00)
    shipping_status = db.Column(db.Enum('chờ giao', 'đang giao', 'đã giao'), default='chờ giao')
    payment_status = db.Column(db.Enum('chờ thanh toán', 'đã thanh toán', 'thất bại'), default='chờ thanh toán')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, customer_id, total_amount=0.00, payment_status='chờ thanh toán'):
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.payment_status = payment_status

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(15, 2), nullable=False)

    def __init__(self, product_id, quantity, price, order_id=None):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        if order_id:
            self.order_id = order_id