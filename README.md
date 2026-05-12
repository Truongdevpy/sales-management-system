# Sales Management System - Phần đã làm

## 1. Làm class User và SellerBankConfig

- Tạo class `User` để quản lý tài khoản trong hệ thống.
- `User` dùng cho đăng nhập, đăng ký, phân quyền `admin`, `seller`, `customer`.
- Seller có thêm trạng thái duyệt: `pending`, `approved`, `rejected`.
- Seller có thông tin shop như tên shop, số điện thoại, địa chỉ, ngành hàng, mô tả shop.
- Tạo class `SellerBankConfig` để lưu cấu hình ngân hàng của từng seller.
- `SellerBankConfig` lưu tên ngân hàng, số tài khoản, tên chủ tài khoản và token API ngân hàng.

File chính:

```text
models/user_model.py
models/payment_model.py
services/user_services.py
```

## 2. Đăng nhập, đăng ký và duyệt seller

- Người dùng có thể đăng ký tài khoản tại trang đăng nhập.
- Nếu đăng ký loại `customer` thì được đăng nhập và sử dụng ngay.
- Nếu đăng ký loại `seller` thì tài khoản ở trạng thái `pending`.
- Seller phải chờ admin duyệt mới đăng nhập được.
- Seller bị `pending` hoặc `rejected` sẽ không được đăng nhập.
- Form đăng ký seller có kiểm tra tên shop trùng, mật khẩu, số điện thoại và thông tin shop.

File chính:

```text
templates/index.html
services/user_services.py
models/user_model.py
```

## 3. Quản lý seller trong admin

- Admin xem danh sách seller.
- Admin duyệt hoặc từ chối seller mới đăng ký.
- Admin tìm kiếm seller theo tên shop, tên chủ shop hoặc tài khoản.
- Admin lọc seller theo trạng thái `pending`, `approved`, `rejected`.
- Admin xem chi tiết seller.
- Admin sửa thông tin seller và trạng thái seller.
- Admin xem cấu hình ngân hàng của seller.

File chính:

```text
templates/admin.html
services/user_services.py
models/user_model.py
static/style.css
```

## 4. Thống kê người mua hàng và phần admin

- Làm các chức năng chính ở phía admin.
- Admin xem thống kê từng shop.
- Thống kê gồm số sản phẩm, số người mua, số đơn hàng và tổng doanh thu.
- Admin xem danh sách sản phẩm của từng seller.
- Admin xem danh sách người mua của từng shop.
- Với mỗi người mua, hệ thống hiển thị số đơn hàng, tổng tiền đã mua và ngày đặt hàng gần nhất.
- Thống kê người mua được tính từ luồng dữ liệu:

```text
users -> orders -> order_items -> products
```

File chính:

```text
templates/admin.html
services/user_services.py
services/customer_services.py
templates/customer-management.html
```

## 5. Thanh toán thật bằng QR ngân hàng

- Thêm hình thức thanh toán chuyển khoản ngân hàng bằng QR.
- Seller tự cấu hình ngân hàng, số tài khoản, tên chủ tài khoản và token API ngân hàng.
- Khi customer đặt hàng bằng chuyển khoản, hệ thống tạo QR theo tài khoản ngân hàng của seller sở hữu sản phẩm.
- Nội dung chuyển khoản do hệ thống tạo, ví dụ `ORD6S9`.
- Khi customer bấm "Tôi đã chuyển khoản", hệ thống gọi API lịch sử giao dịch ngân hàng:

```text
https://thueapi.pro/historyapimbbankv2/<token>
```

- Hệ thống chỉ xác nhận thanh toán thành công khi giao dịch thỏa cả 3 điều kiện:
  - giao dịch là tiền vào: `type = IN`
  - số tiền chuyển khoản đúng bằng tổng tiền đơn hàng
  - nội dung chuyển khoản có chứa đúng mã thanh toán của đơn
- Nếu không tìm thấy giao dịch khớp, hệ thống báo người dùng chưa chuyển khoản hoặc giao dịch chưa đúng nội dung/số tiền.

File chính:

```text
models/payment_model.py
services/order_services.py
templates/checkout.html
templates/track-order.html
templates/seller-bank-config.html
```
