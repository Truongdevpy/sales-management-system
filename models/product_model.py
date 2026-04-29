from . import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False) # ID của Seller
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(15, 2), nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))

    def __init__(self, user_id, name, price, description=None, image_url=None, quantity=0, category=None):
        self.user_id = user_id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url
        self.quantity = quantity
        self.category = category

    def to_dict(self):
        # Chuyển đổi dữ liệu từ Database thành JSON cho Frontend
        return {
            "id": self.id,
            "sellerId": self.user_id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "image": self.image_url, # Giao diện checkout.html đang dùng 'image'
            "stock": self.quantity,  # Giao diện checkout.html đang dùng 'stock'
            "category": self.category,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }