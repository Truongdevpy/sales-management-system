# Sales Management System

Hệ thống quản lý bán hàng được xây dựng bằng Flask, Flask-SQLAlchemy, MySQL, HTML, CSS và JavaScript. Dự án hỗ trợ ba nhóm người dùng chính: admin, seller và customer.

## Chức năng chính

### 1. Tài khoản, phân quyền và session

- Đăng nhập, đăng ký tài khoản.
- Phân quyền người dùng theo `admin`, `seller`, `customer`.
- Customer đăng ký xong có thể đăng nhập ngay.
- Seller đăng ký xong ở trạng thái `pending` và phải chờ admin duyệt.
- Seller bị `pending` hoặc `rejected` không được đăng nhập.
- Đăng nhập sử dụng Flask session/cookie để lưu trạng thái người dùng phía server.
- Có API kiểm tra session hiện tại và đăng xuất.

File liên quan:

```text
models/user_model.py
services/user_services.py
templates/index.html
static/app.js
```

### 2. Quản lý seller trong admin

- Admin xem danh sách seller.
- Duyệt hoặc từ chối seller mới đăng ký.
- Tìm kiếm seller theo tên shop, tên chủ shop hoặc tài khoản.
- Lọc seller theo trạng thái `pending`, `approved`, `rejected`.
- Xem chi tiết seller và cập nhật thông tin seller.
- Xem cấu hình ngân hàng của seller.

File liên quan:

```text
templates/admin.html
services/user_services.py
models/user_model.py
static/style.css
```

### 3. Customer Manager

- Admin quản lý danh sách customer từ bảng `users` với `role = customer`.
- Tìm kiếm customer theo tên, username, số điện thoại hoặc địa chỉ.
- Lọc customer theo trạng thái có đơn hàng hoặc chưa có đơn hàng.
- Xem chi tiết customer.
- Sửa thông tin customer: họ tên, username, số điện thoại, địa chỉ, mật khẩu.
- Xóa tài khoản customer.
- Hiển thị thống kê số đơn, số sản phẩm đã mua, tổng tiền đã chi và ngày đặt hàng gần nhất.
- Các API quản lý customer yêu cầu session admin.

File liên quan:

```text
services/customer_services.py
templates/customer-management.html
static/app.js
```

### 4. Quản lý sản phẩm

- Xem danh sách sản phẩm.
- Thêm, sửa, xóa sản phẩm.
- Tìm kiếm sản phẩm.
- Lọc sản phẩm theo trạng thái tồn kho.
- Upload ảnh sản phẩm.
- Admin có thể quản lý toàn bộ sản phẩm.
- Seller quản lý sản phẩm thuộc shop của mình.

File liên quan:

```text
models/product_model.py
services/product_services.py
templates/product-management.html
static/app.js
```

### 5. Quản lý đơn hàng và vận chuyển

- Lưu đơn hàng và chi tiết sản phẩm trong từng đơn.
- Theo dõi trạng thái thanh toán và trạng thái giao hàng.
- Seller xem đơn hàng của shop mình.
- Chỉ cho xác nhận giao hàng khi đơn đã thanh toán.
- Hiển thị hóa đơn và lịch sử đơn hàng cho customer.

File liên quan:

```text
models/order_model.py
services/order_services.py
templates/order-management.html
templates/track-order.html
templates/invoice.html
```

### 6. Thống kê shop và người mua hàng

- Admin xem thống kê từng shop.
- Thống kê số sản phẩm, số người mua, số đơn hàng và tổng doanh thu.
- Xem danh sách sản phẩm của từng seller.
- Xem danh sách người mua của từng shop.
- Thống kê số đơn, tổng tiền đã mua và ngày đặt hàng gần nhất của từng người mua.

Luồng dữ liệu thống kê:

```text
users -> orders -> order_items -> products
```

File liên quan:

```text
templates/admin.html
services/user_services.py
services/customer_services.py
```

### 7. Thanh toán

Hệ thống hỗ trợ nhiều hình thức thanh toán, gồm thanh toán khi nhận hàng và chuyển khoản ngân hàng bằng QR.

Với thanh toán chuyển khoản:

- Seller cấu hình ngân hàng, số tài khoản, tên chủ tài khoản và token API ngân hàng.
- Hệ thống tạo QR theo đúng tài khoản ngân hàng của seller sở hữu sản phẩm.
- Mỗi đơn hàng có mã nội dung chuyển khoản riêng.
- Khi customer bấm xác nhận đã thanh toán, hệ thống gọi API lịch sử giao dịch ngân hàng.
- Thanh toán chỉ thành công khi giao dịch là tiền vào, đúng số tiền và đúng nội dung chuyển khoản.

File liên quan:

```text
models/payment_model.py
services/order_services.py
templates/checkout.html
templates/track-order.html
templates/seller-bank-config.html
```

## Cấu trúc database

Các bảng chính:

```text
users
products
customers
orders
order_items
seller_bank_configs
payments
```

File SQL:

```text
sales-management-system.sql
```

## Cài đặt và chạy dự án

1. Cài thư viện:

```bash
pip install -r requirements.txt
```

2. Import database MySQL từ file:

```text
sales-management-system.sql
```

3. Chạy server:

```bash
python main.py
```

4. Mở trình duyệt:

```text
http://127.0.0.1:5001
```

Một số trang chính:

```text
/admin
/dashboard
/product-management
/customer-management
/order-management
/checkout
/track-order
```

## Ghi chú

- File `main.py` có cấu hình session/cookie và phần kiểm tra, bổ sung một số cột/bảng cần thiết khi chạy dự án.
- Seller cần cấu hình ngân hàng trước khi dùng thanh toán chuyển khoản bằng QR.
- Token ngân hàng dùng để rà soát lịch sử giao dịch khi customer xác nhận đã chuyển khoản.
