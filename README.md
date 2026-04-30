# Sales Management System - Ghi chú chức năng đã làm

Cập nhật ngày: 2026-04-30

## Tổng quan

Dự án là hệ thống quản lý bán hàng dùng Flask, Flask-SQLAlchemy và MySQL. Các phần đã bổ sung tập trung vào đăng ký tài khoản, duyệt seller, quản lý seller trong admin và thống kê người mua hàng theo shop.

## Chức năng đã làm

### 1. Đăng ký tài khoản

- Thêm form đăng ký tại trang đăng nhập.
- Người dùng đăng ký loại `Customer` được dùng tài khoản ngay.
- Người dùng đăng ký loại `Seller` sẽ ở trạng thái `pending`, cần admin duyệt trước khi đăng nhập.
- Seller bị `pending` hoặc `rejected` sẽ không đăng nhập được.

File liên quan:

- `templates/index.html`
- `services/user_services.py`
- `models/user_model.py`

### 2. Admin duyệt seller

- Admin xem danh sách seller đang chờ duyệt.
- Admin có thể approve hoặc reject seller.
- Sau khi approve, seller có thể đăng nhập và sử dụng chức năng shop.

API liên quan:

```text
GET  /api/users/seller-requests
POST /api/users/seller-requests/<seller_id>/approved
POST /api/users/seller-requests/<seller_id>/rejected
```

File liên quan:

- `templates/admin.html`
- `services/user_services.py`

### 3. Quản lý seller trong admin

- Thêm tab `Seller Management` trong trang admin.
- Có thể tìm kiếm seller theo tên shop, tên chủ hoặc username/email.
- Có thể lọc seller theo trạng thái:
  - `pending`
  - `approved`
  - `rejected`
- Có thể xem chi tiết seller.
- Có thể sửa:
  - tên chủ shop
  - username/email
  - tên shop
  - trạng thái seller

API liên quan:

```text
GET   /api/users/seller-management
GET   /api/users/seller-management/<seller_id>
PUT   /api/users/seller-management/<seller_id>
PATCH /api/users/seller-management/<seller_id>
```

File liên quan:

- `templates/admin.html`
- `static/style.css`
- `services/user_services.py`
- `models/user_model.py`

### 4. Thống kê người mua hàng của shop

- Admin xem thống kê từng shop:
  - số sản phẩm
  - số người mua
  - số đơn hàng
  - tổng doanh thu
- Trong chi tiết seller, admin xem được:
  - danh sách sản phẩm của shop
  - danh sách người mua của shop
  - số đơn từng người mua
  - tổng tiền từng người mua đã chi
  - ngày đặt hàng gần nhất

API liên quan:

```text
GET /api/users/sellers
GET /api/users/seller-buyer-stats
GET /api/users/sellers/<seller_id>/buyers
```

File liên quan:

- `templates/admin.html`
- `services/user_services.py`

### 5. Giao diện admin đã cập nhật

Trang `/admin` hiện có 3 tab:

- `Seller Requests`: duyệt seller mới đăng ký.
- `Seller Management`: quản lý, tìm kiếm, lọc và sửa seller.
- `Shop Statistics`: xem thống kê người mua, đơn hàng và doanh thu theo shop.

File liên quan:

- `templates/admin.html`
- `static/style.css`

## Model/API đã thêm

### User model

Thêm file:

```text
models/user_model.py
```

Model `User` đại diện cho bảng `users`, dùng cho:

- đăng ký
- đăng nhập
- phân quyền customer/seller/admin
- trạng thái duyệt seller
- tên shop seller

### User service

Thêm file:

```text
services/user_services.py
```

Service này xử lý:

- đăng ký tài khoản
- đăng nhập
- duyệt seller
- quản lý seller
- thống kê shop
- danh sách người mua của shop

## Lưu ý database

Các chức năng seller cần dữ liệu trạng thái seller và tên shop. Code hiện dùng:

```text
seller_status
shop_name
```

Nếu database cũ chưa có 2 cột này, phần `ensure_user_schema()` trong `main.py` sẽ tự thêm khi chạy `python main.py`.

## Cách kiểm tra nhanh

Chạy server:

```powershell
python main.py
```

Mở trang:

```text
http://127.0.0.1:5000
http://127.0.0.1:5000/admin
```

Luồng test:

1. Đăng ký tài khoản `Customer`, kiểm tra đăng nhập được ngay.
2. Đăng ký tài khoản `Seller`, kiểm tra bị chờ duyệt.
3. Đăng nhập admin.
4. Vào `/admin`, tab `Seller Requests`, approve seller.
5. Đăng nhập seller vừa được duyệt.
6. Vào `/admin`, tab `Seller Management` và `Shop Statistics` để xem thống kê.

## Thành viên 1 - Quản lý Sản phẩm & Khách hàng

Trạng thái sau khi cập nhật: **đã hoàn thiện các phần chính được giao**.

### Đối chiếu yêu cầu

Yêu cầu trong phân công:

- Front-end: thiết kế Dashboard tổng quát và trang quản lý danh sách Sản phẩm/Khách hàng, có bảng dữ liệu và nút Thêm/Sửa/Xóa.
- Back-end: viết API CRUD cho Sản phẩm và Khách hàng.
- Database: thiết kế cấu trúc bảng `products` và `customers` trong MySQL.
- Báo cáo: viết phần "Phân tích yêu cầu" và "Mô tả chức năng".

### Những phần đã hoàn thiện

#### 1. Dashboard tổng quan

- Dashboard hiển thị số liệu tổng quan thật từ API.
- Với admin:
  - tổng số sản phẩm
  - số sản phẩm còn hàng
  - tổng số khách hàng
  - số khách hàng active
- Với seller:
  - tổng sản phẩm của seller
  - sản phẩm còn hàng
  - sản phẩm hết hàng

File liên quan:

- `templates/dashboard.html`

#### 2. Quản lý sản phẩm

Đã bổ sung trang:

```text
/product-management
```

Chức năng:

- xem danh sách sản phẩm
- tìm kiếm sản phẩm
- lọc sản phẩm theo trạng thái tồn kho
- thêm sản phẩm
- sửa sản phẩm
- xóa sản phẩm
- upload ảnh sản phẩm
- admin có thể quản lý toàn bộ sản phẩm
- seller chỉ quản lý sản phẩm của mình

API liên quan:

```text
GET    /api/products/
GET    /api/products/<product_id>
GET    /api/products/seller/<seller_id>
POST   /api/products/
PUT    /api/products/<product_id>
PATCH  /api/products/<product_id>
DELETE /api/products/<product_id>
```

File liên quan:

- `models/product_model.py`
- `services/product_services.py`
- `templates/product-management.html`
- `static/app.js`
- `main.py`

#### 3. Quản lý khách hàng

Đã bổ sung model và trang:

```text
/customer-management
```

Chức năng:

- xem danh sách khách hàng
- tìm kiếm theo tên, email, số điện thoại, địa chỉ
- lọc theo trạng thái `active` hoặc `inactive`
- thêm khách hàng
- sửa khách hàng
- xóa khách hàng
- thống kê tổng khách hàng, active, inactive

API liên quan:

```text
GET    /api/customers/
GET    /api/customers/stats
GET    /api/customers/<customer_id>
POST   /api/customers/
PUT    /api/customers/<customer_id>
PATCH  /api/customers/<customer_id>
DELETE /api/customers/<customer_id>
```

File liên quan:

- `models/customer_model.py`
- `services/customer_services.py`
- `templates/customer-management.html`
- `static/app.js`
- `main.py`

#### 4. Cấu trúc bảng MySQL

Hai bảng đã có trong SQL:

```text
products
customers
```

Bảng `products` dùng cho:

- mã sản phẩm
- seller sở hữu sản phẩm
- tên sản phẩm
- mô tả
- giá
- ảnh
- số lượng tồn kho
- danh mục
- ngày tạo

Bảng `customers` dùng cho:

- mã khách hàng
- họ tên
- email
- số điện thoại
- địa chỉ
- trạng thái
- ngày tạo

File liên quan:

- `sales-management-system.sql`
- `models/product_model.py`
- `models/customer_model.py`

### Phân tích yêu cầu

Hệ thống cần cho phép quản trị viên và seller quản lý dữ liệu sản phẩm, đồng thời cho phép quản trị viên quản lý danh sách khách hàng. Dữ liệu cần được lưu trong MySQL, truy xuất qua API Flask và hiển thị dưới dạng bảng để người dùng dễ thao tác.

Đối tượng sử dụng chính:

- Admin: quản lý toàn bộ sản phẩm và toàn bộ khách hàng.
- Seller: quản lý sản phẩm thuộc shop của mình.
- Customer: xem sản phẩm và mua hàng.

Nhu cầu nghiệp vụ:

- Sản phẩm phải có thông tin tên, giá, số lượng, danh mục, mô tả và ảnh.
- Khách hàng phải có thông tin họ tên, email, số điện thoại, địa chỉ và trạng thái.
- Admin cần xem nhanh số lượng sản phẩm/khách hàng trên Dashboard.
- Người dùng quản trị cần thao tác thêm, sửa, xóa nhanh ngay trên giao diện bảng.

### Mô tả chức năng

#### Chức năng quản lý sản phẩm

Người dùng có quyền truy cập trang quản lý sản phẩm để xem danh sách sản phẩm dưới dạng bảng. Mỗi dòng sản phẩm hiển thị ảnh, tên, danh mục, giá, tồn kho, seller và trạng thái còn hàng/hết hàng.

Các thao tác chính:

- Thêm sản phẩm mới bằng form.
- Cập nhật thông tin sản phẩm.
- Upload hoặc thay đổi ảnh sản phẩm.
- Xóa sản phẩm khỏi hệ thống.
- Lọc sản phẩm còn hàng/hết hàng.
- Tìm kiếm sản phẩm theo tên hoặc danh mục.

#### Chức năng quản lý khách hàng

Admin truy cập trang quản lý khách hàng để xem danh sách khách hàng dưới dạng bảng. Mỗi dòng hiển thị mã khách hàng, họ tên, email, số điện thoại, địa chỉ, trạng thái và ngày tạo.

Các thao tác chính:

- Thêm khách hàng mới.
- Cập nhật thông tin khách hàng.
- Đổi trạng thái active/inactive.
- Xóa khách hàng.
- Tìm kiếm khách hàng theo tên, email, số điện thoại hoặc địa chỉ.
- Lọc khách hàng theo trạng thái.

#### Chức năng Dashboard tổng quan

Dashboard cung cấp số liệu nhanh để người dùng nắm tình hình dữ liệu:

- Admin xem tổng sản phẩm, sản phẩm còn hàng, tổng khách hàng và khách hàng đang active.
- Seller xem tổng sản phẩm của mình, số sản phẩm còn hàng và hết hàng.

### Kết luận phần Thành viên 1

Phần **Quản lý Sản phẩm & Khách hàng** đã hoàn thiện các yêu cầu chính:

- Có giao diện Dashboard tổng quan.
- Có giao diện quản lý danh sách sản phẩm.
- Có giao diện quản lý danh sách khách hàng.
- Có nút thêm/sửa/xóa trên giao diện.
- Có API CRUD sản phẩm.
- Có API CRUD khách hàng.
- Có model tương ứng với bảng `products` và `customers`.
- Có nội dung báo cáo gồm phân tích yêu cầu và mô tả chức năng.
