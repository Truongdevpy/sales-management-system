from flask import Flask, render_template
from sqlalchemy import text
from models import db
from services.order_services import order_bp
from services.user_services import user_bp
from services.customer_services import customer_bp

app = Flask(__name__)

# 1. CẤU HÌNH DATABASE
# Lưu ý: Xóa dấu :"" nếu bạn dùng XAMPP mặc định không mật khẩu
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost/sales-management-system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo db với app
db.init_app(app)

# 2. ĐĂNG KÝ BLUEPRINT (Cho các API xử lý dữ liệu)
app.register_blueprint(order_bp, url_prefix='/api/orders')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(customer_bp, url_prefix='/api/customers')


# Import product blueprint
from services.product_services import product_bp

# Đăng ký blueprint cho API Products
app.register_blueprint(product_bp, url_prefix='/api/products')




def ensure_user_schema():
    result = db.session.execute(text("SHOW COLUMNS FROM users")).fetchall()
    columns = {row[0] for row in result}

    if 'seller_status' not in columns:
        db.session.execute(text(
            "ALTER TABLE users "
            "ADD seller_status ENUM('pending','approved','rejected') DEFAULT 'approved'"
        ))

    if 'shop_name' not in columns:
        db.session.execute(text("ALTER TABLE users ADD shop_name VARCHAR(100) DEFAULT NULL"))

    db.session.execute(text(
        "UPDATE users SET seller_status = 'approved' WHERE seller_status IS NULL"
    ))
    db.session.commit()

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

@app.route('/product-management')
def product_management():
    return render_template('product-management.html')

@app.route('/customer-management')
def customer_management():
    return render_template('customer-management.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/track-order')
def track_order():
    return render_template('track-order.html')

# --- ROUTE MỚI ĐƯỢC THÊM VÀO ĐỂ KHÔNG BỊ LỖI 404 ---
@app.route('/product-detail')
def product_detail():
    return render_template('product-detail.html')

@app.route('/manage-orders')
def manage_orders():
    return render_template('order-management.html')

# 4. CHẠY ỨNG DỤNG
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_user_schema()
    # Chạy trên port 5001 để tránh xung đột hệ thống
    app.run(debug=True, port=5001
)
