class User:
    def __init__(self, data_dict):
        # Biến Dictionary từ Database thành các thuộc tính của đối tượng
        self.id = data_dict.get('id')
        self.full_name = data_dict.get('full_name')
        self.username = data_dict.get('username')
        self.password = data_dict.get('password')
        self.role = data_dict.get('role', 'customer')

    # Kiểm tra xem User này có quyền đăng hàng không
    def can_sell(self):
        return self.role in ['seller', 'admin']

    @staticmethod
    def find_by_auth(cursor, username, password):
        """Hàm dùng cho đăng nhập"""
        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(sql, (username, password))
        row = cursor.fetchone()
        return User(row) if row else None

    @staticmethod
    def create(cursor, db, full_name, username, password, role='customer'):
        """Hàm dùng cho đăng ký"""
        sql = "INSERT INTO users (full_name, username, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (full_name, username, password, role))
        db.commit()


class Product:
    def __init__(self, data_dict):
        self.id = data_dict.get('id')
        self.user_id = data_dict.get('user_id')
        self.name = data_dict.get('name')
        self.description = data_dict.get('description')
        self.price = data_dict.get('price', 0)
        self.image_url = data_dict.get('image_url')
        self.quantity = data_dict.get('quantity', 0)

    def format_price(self):
        return "{:,.0f} VNĐ".format(self.price)

    @staticmethod
    def get_all(cursor):
        """Lấy toàn bộ sản phẩm mới nhất"""
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        return [Product(row) for row in cursor.fetchall()]

    @staticmethod
    def find_by_id(cursor, product_id):
        """Lấy chi tiết 1 sản phẩm"""
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        return Product(row) if row else None

    @staticmethod
    def search(cursor, keyword):
        """Tìm kiếm sản phẩm theo tên hoặc mô tả"""
        sql = "SELECT * FROM products WHERE name LIKE %s OR description LIKE %s ORDER BY id DESC"
        search_term = f"%{keyword}%"
        cursor.execute(sql, (search_term, search_term))
        return [Product(row) for row in cursor.fetchall()]

    @staticmethod
    def delete(cursor, db, product_id):
        """Xóa sản phẩm"""
        sql = "DELETE FROM products WHERE id = %s"
        cursor.execute(sql, (product_id,))
        db.commit()

    @staticmethod
    def add(cursor, db, user_id, name, desc, price, img, qty):
        """Thêm sản phẩm mới"""
        sql = """INSERT INTO products (user_id, name, description, price, image_url, quantity) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (user_id, name, desc, price, img, qty))
        db.commit()