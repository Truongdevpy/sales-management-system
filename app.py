import os
from flask import Flask, render_template, request, redirect, session, url_for
import pymysql
import config 
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'tuan'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset=config.DB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Lỗi kết nối Database: {e}")
        return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        password = request.form.get('password')
        role = 'customer' 

        db = get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    sql = "INSERT INTO users (full_name, username, password, role) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (full_name, username, password, role))
                    db.commit()
                return redirect(url_for('login'))
            except Exception as e:
                return f"<h1>Lỗi: {e}</h1>"
            finally:
                db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db_connection()
        if db:
            try:
                with db.cursor() as cursor:
                    sql = "SELECT * FROM users WHERE username = %s AND password = %s"
                    cursor.execute(sql, (username, password))
                    user = cursor.fetchone()
                    
                    if user:
                        session['user_id'] = user['id']
                        session['username'] = user['username']
                        session['role'] = user['role']
                        
                        return redirect(url_for('create'))
                    else:
                        return "<h1>Sai tài khoản hoặc mật khẩu! ❌</h1>"
            finally:
                db.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') not in ['seller', 'admin']:
        return "<h1>Bạn không có quyền đăng sản phẩm! ❌</h1>", 403

    db = get_db_connection()
    cursor = db.cursor()

    if request.method == 'POST':
        ten_san_pham = request.form.get('ten_san_pham')
        gia_ban = request.form.get('gia_ban')
        mo_ta = request.form.get('mo_ta')
        file_anh = request.files.get('anh_san_pham')
        so_luong = request.form.get('so_luong') or 0

        filename = ""
        if file_anh and file_anh.filename != '':
            filename = secure_filename(file_anh.filename)
            file_anh.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        try:
            sql = """INSERT INTO products (user_id, name, description, price, image_url, quantity) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (session['user_id'], ten_san_pham, mo_ta, gia_ban, filename, so_luong))
            db.commit()
            return redirect(url_for('list_item')) 
        except Exception as e:
            return f"<h1>Lỗi SQL: {e}</h1>"
        finally:
            db.close()


    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    all_products = cursor.fetchall()
    db.close()
    
    return render_template('create.html', products=all_products)

@app.route('/list_item')
def list_item():
    db = get_db_connection()
    products = []
    if db:
        try:
            with db.cursor() as cursor:
                sql = "SELECT * FROM products ORDER BY id DESC"
                cursor.execute(sql)
                products = cursor.fetchall()
        except Exception as e:
            print(f"Lỗi lấy dữ liệu: {e}")
        finally:
            db.close()
    
    return render_template('list_item.html', products=products)

@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    db = get_db_connection()
    if db:
        try:
            with db.cursor() as cursor:
                sql = "DELETE FROM products WHERE id = %s"
                cursor.execute(sql, (product_id,))
                db.commit()
        except Exception as e:
            return f"<h1>Lỗi SQL: {e}</h1>"
        finally:
            db.close()
    
    return redirect(url_for('list_item'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db_connection()
    product = None
    if db:
        try:
            with db.cursor() as cursor:
                sql = "SELECT * FROM products WHERE id = %s"
                cursor.execute(sql, (product_id,))
                product = cursor.fetchone()
        finally:
            db.close()

    if product:
        return render_template('product_detail.html', product=product)
    return "<h1>Sản phẩm không tồn tại! ❌</h1>", 404

@app.route('/search')
def search():
    keyword = request.args.get('query', '').strip()
    
    db = get_db_connection()
    products = []
    
    if db:
        try:
            with db.cursor() as cursor:
                if keyword:
                    sql = """SELECT * FROM products 
                             WHERE name LIKE %s OR description LIKE %s 
                             ORDER BY id DESC"""
                    search_term = f"%{keyword}%"
                    cursor.execute(sql, (search_term, search_term))
                else:
                    cursor.execute("SELECT * FROM products ORDER BY id DESC")
                
                products = cursor.fetchall()
        finally:
            db.close()
            
    return render_template('list_item.html', products=products, query=keyword)

if __name__ == '__main__':
    app.run(debug=True, port=5001)