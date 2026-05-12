from datetime import datetime

from . import db


class SellerBankConfig(db.Model):
    __tablename__ = 'seller_bank_configs'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    bank_name = db.Column(db.String(100))
    bank_acq_id = db.Column(db.String(20))
    account_no = db.Column(db.String(50), nullable=False)
    account_name = db.Column(db.String(120), nullable=False)
    vietqr_client_id = db.Column(db.String(120))
    vietqr_api_key = db.Column(db.String(255))
    bank_history_token = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "sellerId": self.seller_id,
            "bankName": self.bank_name,
            "bankAcqId": self.bank_acq_id,
            "accountNo": self.account_no,
            "accountName": self.account_name,
            "vietqrClientId": self.vietqr_client_id,
            "vietqrApiKey": self.vietqr_api_key,
            "bankHistoryToken": self.bank_history_token,
            "isActive": bool(self.is_active),
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, unique=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    method = db.Column(db.Enum('cod', 'bank_transfer'), nullable=False, default='cod')
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_code = db.Column(db.String(50), unique=True)
    qr_data_url = db.Column(db.Text)
    qr_content = db.Column(db.String(255))
    status = db.Column(db.Enum('pending', 'paid', 'failed'), nullable=False, default='pending')
    matched_transaction_id = db.Column(db.String(100))
    matched_description = db.Column(db.Text)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        from models.user_model import User

        bank_config = None
        seller = db.session.get(User, self.seller_id) if self.seller_id else None
        if self.method == 'bank_transfer' and self.seller_id:
            bank_config = SellerBankConfig.query.filter_by(
                seller_id=self.seller_id,
                is_active=True,
            ).first()

        return {
            "id": self.id,
            "orderId": self.order_id,
            "sellerId": self.seller_id,
            "sellerName": seller.full_name if seller else None,
            "shopName": seller.shop_name if seller else None,
            "method": self.method,
            "amount": float(self.amount or 0),
            "paymentCode": self.payment_code,
            "qrDataUrl": self.qr_data_url,
            "qrContent": self.qr_content,
            "status": self.status,
            "matchedTransactionId": self.matched_transaction_id,
            "paidAt": self.paid_at.strftime("%Y-%m-%d %H:%M:%S") if self.paid_at else None,
            "bankName": bank_config.bank_name if bank_config else None,
            "bankAcqId": bank_config.bank_acq_id if bank_config else None,
            "accountNo": bank_config.account_no if bank_config else None,
            "accountName": bank_config.account_name if bank_config else None,
        }
