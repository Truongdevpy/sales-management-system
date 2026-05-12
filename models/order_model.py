from datetime import datetime

from . import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    shipping_status = db.Column(db.Enum('chờ giao', 'đang giao', 'đã giao'), default='chờ giao')
    payment_status = db.Column(db.Enum('chờ thanh toán', 'đã thanh toán', 'thất bại'), default='chờ thanh toán')
    created_at = db.Column(db.DateTime, default=datetime.now)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __init__(self, customer_id, total_amount=0, payment_status='chờ thanh toán', shipping_status='chờ giao'):
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.payment_status = payment_status
        self.shipping_status = shipping_status


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(15, 2), nullable=False)

    product = db.relationship('Product', back_populates='order_items', lazy=True)

    def __init__(self, order_id, product_id, quantity, price):
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
