from flask import Flask, render_template
from models import db
from services.order_services import order_bp

app = Flask(__name__)

# 1. CẤU HÌNH DATABASE
# Lưu ý: Xóa dấu :"" nếu bạn dùng XAMPP mặc định không mật khẩu
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost/sales-management-system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo db với app
db.init_app(app)

# 2. ĐĂNG KÝ BLUEPRINT (Cho các API xử lý dữ liệu)
app.register_blueprint(order_bp, url_prefix='/api/orders')

# 3. CÁC ROUTE ĐỂ HIỂN THỊ GIAO DIỆN (FRONTEND)

@app.route('/')
def index():
    # Trả về trang đăng nhập
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/seller')
def seller():
    return render_template('seller.html')

@app.route('/shop-products')
def shop_products():
    return render_template('shop-products.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/track-order')
def track_order():
    return render_template('track-order.html')

# 4. CHẠY ỨNG DỤNG
if __name__ == '__main__':
    with app.app_context():
        # Tự động tạo bảng nếu chưa có (nhớ tạo database trong phpMyAdmin trước)
        db.create_all()
    app.run(debug=True)