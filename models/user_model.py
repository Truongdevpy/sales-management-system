from . import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(db.Enum('admin', 'customer', 'seller'), default='customer')
    seller_status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='approved')
    shop_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    business_type = db.Column(db.String(100))
    shop_description = db.Column(db.Text)

    def __init__(
        self,
        username,
        password,
        full_name=None,
        role='customer',
        seller_status='approved',
        shop_name=None,
        phone=None,
        address=None,
        business_type=None,
        shop_description=None,
    ):
        self.username = username
        self.password = password
        self.full_name = full_name
        self.role = role
        self.seller_status = seller_status
        self.shop_name = shop_name
        self.phone = phone
        self.address = address
        self.business_type = business_type
        self.shop_description = shop_description

    def to_session_dict(self):
        display_name = self.full_name or self.username
        return {
            "id": self.id,
            "name": display_name,
            "email": self.username,
            "role": self.role,
            "avatar": display_name[:1].upper() if display_name else "U",
            "shopName": self.shop_name,
            "sellerStatus": self.seller_status,
            "phone": self.phone,
            "address": self.address,
        }

    def to_seller_review_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "shopName": self.shop_name or self.full_name or self.username,
            "fullName": self.full_name,
            "ownerName": self.full_name or self.username,
            "email": self.username,
            "phone": self.phone,
            "address": self.address,
            "businessType": self.business_type,
            "shopDescription": self.shop_description,
            "status": self.seller_status,
            "date": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

    def to_seller_management_dict(self, stats=None):
        stats = stats or {}
        return {
            "id": self.id,
            "username": self.username,
            "email": self.username,
            "fullName": self.full_name,
            "shopName": self.shop_name or self.full_name or self.username,
            "phone": self.phone,
            "address": self.address,
            "businessType": self.business_type,
            "shopDescription": self.shop_description,
            "status": self.seller_status,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "totalProducts": int(stats.get("totalProducts", 0)),
            "totalBuyers": int(stats.get("totalBuyers", 0)),
            "totalOrders": int(stats.get("totalOrders", 0)),
            "totalSales": float(stats.get("totalSales", 0)),
        }
