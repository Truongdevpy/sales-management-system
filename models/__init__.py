from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .order_model import Order, OrderItem