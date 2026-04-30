import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        # Thiết lập cấu hình kết nối
        connection = mysql.connector.connect(
            host='localhost',
            database='sales-management-system', 
            user='root', 
            password='' 
        )

        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"Đã kết nối thành công với MySQL Server phiên bản: {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"Bạn đang kết nối với database: {record}")

    except Error as e:
        print(f"Lỗi khi kết nối MySQL: {e}")
    
    finally:
        # Luôn đóng kết nối khi hoàn tất
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Kết nối MySQL đã được đóng.")

if __name__ == "__main__":
    connect_to_database()