from models import db, Order, OrderItem

class OrderService:
    """Lớp xử lý nghiệp vụ cho Đơn hàng và Thanh toán"""

    def __init__(self, db_session):
        self.db = db_session

    def place_order(self, customer_id, cart_data, payment_method_info=None):
        """
        Hàm thực hiện đặt hàng.
        cart_data: danh sách dạng [{'product_id': 8, 'quantity': 1, 'price': 1725000}, ...]
        """
        try:
            # 1. Tạo đơn hàng mới dựa trên bảng orders trong SQL
            new_order = Order(
                customer_id=customer_id,
                total_amount=0,
                payment_status='chờ thanh toán'
            )
            self.db.add(new_order)
            self.db.flush() # Lấy ID đơn hàng ngay để làm khóa ngoại cho Item

            final_total = 0

            # 2. Tạo các bản ghi chi tiết đơn hàng (order_items)
            for item in cart_data:
                subtotal = item['price'] * item['quantity']
                final_total += subtotal
                
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                self.db.add(order_item)

            # 3. Cập nhật tổng tiền cuối cùng vào đơn hàng
            new_order.total_amount = final_total
            
            self.db.commit()
            return {"status": "success", "order_id": new_order.id, "total": float(final_total)}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def confirm_payment(self, order_id):
        """Cập nhật trạng thái payment_status thành 'đã thanh toán'"""
        order = Order.query.get(order_id)
        if order:
            order.payment_status = 'đã thanh toán'
            self.db.commit()
            return True
        return False