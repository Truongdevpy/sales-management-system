import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import db
from models.product_model import Product

class ProductService:
    def __init__(self, db_session):
        self.db = db_session

    def get_all_products(self):
        products = self.db.session.query(Product).all()
        return [p.to_dict() for p in products]

    def get_products_by_seller(self, seller_id):
        products = self.db.session.query(Product).filter(Product.user_id == seller_id).all()
        return [p.to_dict() for p in products]

    def add_product(self, data):
        try:
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
            return {"status": "success", "product_id": new_product.id, "message": "Thêm sản phẩm thành công"}
        except Exception as e:
            self.db.session.rollback()
            return {"status": "error", "message": str(e)}

product_bp = Blueprint('product_bp', __name__)

@product_bp.route('/', methods=['GET'])
def api_get_all_products():
    service = ProductService(db)
    products = service.get_all_products()
    return jsonify(products), 200

@product_bp.route('/seller/<int:seller_id>', methods=['GET'])
def api_get_seller_products(seller_id):
    service = ProductService(db)
    products = service.get_products_by_seller(seller_id)
    return jsonify(products), 200

# ROUTE ĐÃ SỬA ĐỂ NHẬN FORMDATA VÀ FILE ẢNH
@product_bp.route('/', methods=['POST'])
def api_add_product():
    try:
        # 1. Lấy dữ liệu văn bản từ request.form (dùng cho FormData)
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        price = request.form.get('price')
        quantity = request.form.get('quantity', 0)
        category = request.form.get('category', '')
        description = request.form.get('description', '')

        if not name or not price:
            return jsonify({"message": "Thiếu tên hoặc giá sản phẩm"}), 400

        # 2. Xử lý file ảnh tải lên
        image_url = ""
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                # Tạo tên file an toàn và lưu vào static/uploads
                filename = secure_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads')
                
                # Tạo thư mục nếu chưa tồn tại
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Lưu đường dẫn vào database để hiển thị trên web
                image_url = f'/static/uploads/{filename}'

        # 3. Gom dữ liệu lại để gọi service
        data = {
            'user_id': user_id,
            'name': name,
            'price': price,
            'description': description,
            'image_url': image_url,
            'quantity': quantity,
            'category': category
        }
        
        service = ProductService(db)
        result = service.add_product(data)

        if result['status'] == 'success':
            return jsonify(result), 201
        return jsonify(result), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500