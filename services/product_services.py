import os

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from models import db
from models.product_model import Product


product_bp = Blueprint('product_bp', __name__)


class ProductService:
    def __init__(self, db_session):
        self.db = db_session

    def get_all_products(self):
        products = self.db.session.query(Product).order_by(Product.created_at.desc()).all()
        return [p.to_dict() for p in products]

    def get_product_by_id(self, product_id):
        product = self.db.session.get(Product, product_id)
        return product.to_dict() if product else None

    def get_products_by_seller(self, seller_id):
        products = (
            self.db.session.query(Product)
            .filter(Product.user_id == seller_id)
            .order_by(Product.created_at.desc())
            .all()
        )
        return [p.to_dict() for p in products]

    def add_product(self, data):
        try:
            error = self._validate_product_data(data, required=True)
            if error:
                return {"status": "error", "message": error}, 400

            new_product = Product(
                user_id=data.get('user_id'),
                name=data.get('name'),
                price=data.get('price'),
                description=data.get('description', ''),
                image_url=data.get('image_url', ''),
                quantity=data.get('quantity', 0),
                category=data.get('category', '')
            )
            self.db.session.add(new_product)
            self.db.session.commit()
            return {
                "status": "success",
                "product_id": new_product.id,
                "product": new_product.to_dict(),
                "message": "Them san pham thanh cong",
            }, 201
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}, 400

    def update_product(self, product_id, data):
        try:
            product = self.db.session.get(Product, product_id)
            if not product:
                return {"status": "error", "message": "Khong tim thay san pham"}, 404

            error = self._validate_product_data(data, required=False)
            if error:
                return {"status": "error", "message": error}, 400

            fields = {
                "user_id": "user_id",
                "name": "name",
                "price": "price",
                "description": "description",
                "image_url": "image_url",
                "quantity": "quantity",
                "category": "category",
            }

            for data_key, model_attr in fields.items():
                value = data.get(data_key)
                if value is not None:
                    setattr(product, model_attr, value)

            self.db.session.commit()
            return {
                "status": "success",
                "product": product.to_dict(),
                "message": "Cap nhat san pham thanh cong",
            }, 200
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}, 400

    def delete_product(self, product_id):
        try:
            product = self.db.session.get(Product, product_id)
            if not product:
                return {"status": "error", "message": "Khong tim thay san pham"}, 404

            self.db.session.delete(product)
            self.db.session.commit()
            return {"status": "success", "message": "Xoa san pham thanh cong"}, 200
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}, 400

    def _validate_product_data(self, data, required=False):
        if required and not data.get('user_id'):
            return "Thieu seller/user_id"

        if required and not data.get('name'):
            return "Thieu ten san pham"

        if required and data.get('price') in (None, ''):
            return "Thieu gia san pham"

        if data.get('price') not in (None, '') and float(data.get('price')) < 0:
            return "Gia san pham khong duoc am"

        if data.get('quantity') not in (None, '') and int(data.get('quantity')) < 0:
            return "So luong san pham khong duoc am"

        return None


def build_product_data_from_request():
    if request.is_json:
        raw = request.get_json() or {}
    else:
        raw = request.form.to_dict()

    data = {
        'user_id': raw.get('user_id'),
        'name': raw.get('name'),
        'price': raw.get('price'),
        'description': raw.get('description', ''),
        'image_url': raw.get('image_url', ''),
        'quantity': raw.get('quantity', 0),
        'category': raw.get('category', ''),
    }

    image_url = save_uploaded_product_image()
    if image_url:
        data['image_url'] = image_url

    return data


def save_uploaded_product_image():
    if 'image' not in request.files:
        return None

    file = request.files['image']
    if file.filename == '':
        return None

    filename = secure_filename(file.filename)
    upload_folder = os.path.join('static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return f'/static/uploads/{filename}'


@product_bp.route('/', methods=['GET'])
def api_get_all_products():
    service = ProductService(db)
    products = service.get_all_products()
    return jsonify(products), 200


@product_bp.route('/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        return jsonify({"message": "Khong tim thay san pham"}), 404
    return jsonify(product), 200


@product_bp.route('/seller/<int:seller_id>', methods=['GET'])
def api_get_seller_products(seller_id):
    service = ProductService(db)
    products = service.get_products_by_seller(seller_id)
    return jsonify(products), 200


@product_bp.route('/', methods=['POST'])
def api_add_product():
    service = ProductService(db)
    result, status_code = service.add_product(build_product_data_from_request())
    return jsonify(result), status_code


@product_bp.route('/<int:product_id>', methods=['PUT', 'PATCH'])
def api_update_product(product_id):
    service = ProductService(db)
    result, status_code = service.update_product(product_id, build_product_data_from_request())
    return jsonify(result), status_code


@product_bp.route('/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    service = ProductService(db)
    result, status_code = service.delete_product(product_id)
    return jsonify(result), status_code
