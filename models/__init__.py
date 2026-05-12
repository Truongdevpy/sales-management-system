from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user_model import User
from .order_model import Order, OrderItem
from .product_model import Product
from .customer_model import Customer
from .payment_model import SellerBankConfig, Payment
