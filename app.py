from curses import flash
import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
import config 
from werkzeug.utils import secure_filename
from models import User, Product 
import pymysql

app = Flask(__name__)
app.secret_key = 'tuan'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    try:
        return pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset=config.DB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    User.create(
                        cursor, db,
                        full_name=request.form.get('full_name'),
                        username=request.form.get('username'),
                        password=request.form.get('password')
                    )
                return redirect(url_for('login'))
            except Exception as e:
                return f"<h1>Lỗi: {e}</h1>"
            finally:
                db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db_connection()
        if db:
            with db.cursor() as cursor:
                user = User.find_by_auth(cursor, request.form.get('username'), request.form.get('password'))
                if user:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['role'] = user.role
                    return redirect(url_for('create'))
                flash('Sai tài khoản hoặc mật khẩu! ❌', 'danger') 
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- PRODUCT ROUTES ---

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = User(session) 
    if not current_user.can_sell():
        return "<h1>Bạn không có quyền đăng sản phẩm! ❌</h1>", 403

    db = get_db_connection()
    if request.method == 'POST':
        file_anh = request.files.get('anh_san_pham')
        filename = ""
        if file_anh and file_anh.filename != '':
            filename = secure_filename(file_anh.filename)
            file_anh.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with db.cursor() as cursor:
            Product.add(
                cursor, db,
                user_id=session['user_id'],
                name=request.form.get('ten_san_pham'),
                desc=request.form.get('mo_ta'),
                price=float(request.form.get('gia_ban', 0)),
                img=filename,
                qty=int(request.form.get('so_luong', 0))
            )
        db.close()
        return redirect(url_for('list_item'))

    with db.cursor() as cursor:
        all_products = Product.get_all(cursor)
    db.close()
    return render_template('create.html', products=all_products)

@app.route('/list_item')
def list_item():
    db = get_db_connection()
    with db.cursor() as cursor:
        products = Product.get_all(cursor)
    db.close()
    return render_template('list_item.html', products=products)

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    db = get_db_connection()
    with db.cursor() as cursor:
        Product.delete(cursor, db, product_id)
    db.close()
    return redirect(url_for('list_item'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db_connection()
    with db.cursor() as cursor:
        product = Product.find_by_id(cursor, product_id)
    db.close()

    if product:
        return render_template('product_detail.html', product=product)
    return "<h1>Sản phẩm không tồn tại! ❌</h1>", 404

@app.route('/search')
def search():
    keyword = request.args.get('query', '').strip()
    db = get_db_connection()
    with db.cursor() as cursor:
        products = Product.search(cursor, keyword)
    db.close()
    return render_template('list_item.html', products=products, query=keyword)


@app.route('/update_product', methods=['POST'])
def update_product():
    product_id = request.form.get('product_id')
    name = request.form.get('name')
    price = request.form.get('price')
    quantity = request.form.get('quantity')

    db = get_db_connection()
    if db:
        try:
            with db.cursor() as cursor:
                # Gọi hàm update trong Model (Bảo nên viết hàm này vào models.py nhé)
                sql = "UPDATE products SET name=%s, price=%s, quantity=%s WHERE id=%s"
                cursor.execute(sql, (name, price, quantity, product_id))
                db.commit()
            flash("Cập nhật sản phẩm thành công! ✅")
        except Exception as e:
            flash(f"Lỗi khi cập nhật: {e}")
        finally:
            db.close()
            
    return redirect(url_for('create')) 
if __name__ == '__main__':
    app.run(debug=True, port=5001)