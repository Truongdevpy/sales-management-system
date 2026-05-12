from . import db
from datetime import datetime


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    status = db.Column(db.Enum('active', 'inactive'), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, full_name, email=None, phone=None, address=None, status='active'):
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.address = address
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "fullName": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "status": self.status,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
