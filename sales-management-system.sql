-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th5 12, 2026 lúc 07:46 AM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `sales-management-system`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `customers`
--

CREATE TABLE `customers` (
  `id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(120) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `customers`
--

INSERT INTO `customers` (`id`, `full_name`, `email`, `phone`, `address`, `status`, `created_at`) VALUES
(1, 'Nguyen Van An', 'an.nguyen@example.com', '0901000001', 'Quan 1, TP. Ho Chi Minh', 'active', '2026-04-22 10:00:00'),
(2, 'Tran Thi Binh', 'binh.tran@example.com', '0901000002', 'Quan Binh Thanh, TP. Ho Chi Minh', 'active', '2026-04-22 10:05:00'),
(3, 'Le Minh Chau', 'chau.le@example.com', '0901000003', 'Thu Duc, TP. Ho Chi Minh', 'inactive', '2026-04-22 10:10:00');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `orders`
--

CREATE TABLE `orders` (
  `id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `total_amount` decimal(15,2) NOT NULL DEFAULT 0.00,
  `shipping_status` enum('chờ giao','đang giao','đã giao') DEFAULT 'chờ giao',
  `payment_status` enum('chờ thanh toán','đã thanh toán','thất bại') DEFAULT 'chờ thanh toán',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `orders`
--

INSERT INTO `orders` (`id`, `customer_id`, `total_amount`, `shipping_status`, `payment_status`, `created_at`) VALUES
(1, 5, 17782776.00, 'chờ giao', 'chờ thanh toán', '2026-05-12 05:19:48'),
(2, 5, 14999.00, 'chờ giao', 'chờ thanh toán', '2026-05-12 05:22:30'),
(3, 5, 14999.00, 'chờ giao', 'chờ thanh toán', '2026-05-12 05:22:55'),
(4, 6, 14999.00, 'chờ giao', 'chờ thanh toán', '2026-05-12 05:26:37'),
(6, 5, 13888.00, 'chờ giao', 'đã thanh toán', '2026-05-12 05:34:52'),
(7, 5, 13888.00, 'chờ giao', 'chờ thanh toán', '2026-05-12 05:40:41'),
(8, 5, 13888.00, 'chờ giao', 'đã thanh toán', '2026-05-12 05:40:52');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `order_items`
--

CREATE TABLE `order_items` (
  `id` int(11) NOT NULL,
  `order_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL DEFAULT 1,
  `price` decimal(15,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `order_items`
--

INSERT INTO `order_items` (`id`, `order_id`, `product_id`, `quantity`, `price`) VALUES
(6, 6, 14, 1, 8888.00),
(7, 7, 14, 1, 8888.00),
(8, 8, 14, 1, 8888.00);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `payments`
--

CREATE TABLE `payments` (
  `id` int(11) NOT NULL,
  `order_id` int(11) NOT NULL,
  `seller_id` int(11) DEFAULT NULL,
  `method` enum('cod','bank_transfer') NOT NULL DEFAULT 'cod',
  `amount` decimal(15,2) NOT NULL,
  `payment_code` varchar(50) DEFAULT NULL,
  `qr_data_url` text DEFAULT NULL,
  `qr_content` varchar(255) DEFAULT NULL,
  `status` enum('pending','paid','failed') NOT NULL DEFAULT 'pending',
  `matched_transaction_id` varchar(100) DEFAULT NULL,
  `matched_description` text DEFAULT NULL,
  `paid_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `payments`
--

INSERT INTO `payments` (`id`, `order_id`, `seller_id`, `method`, `amount`, `payment_code`, `qr_data_url`, `qr_content`, `status`, `matched_transaction_id`, `matched_description`, `paid_at`, `created_at`, `updated_at`) VALUES
(1, 1, 9, 'bank_transfer', 17782776.00, 'ORD1S9', 'https://img.vietqr.io/image/970422-0868133346-compact.png?amount=17782776&addInfo=ORD1S9&accountName=Nguy%E1%BB%85n%20V%C4%83n%20Tr%C6%B0%E1%BB%9Dng', 'ORD1S9', 'pending', NULL, NULL, NULL, '2026-05-12 05:19:48', '2026-05-12 05:19:48'),
(2, 2, 1, 'cod', 14999.00, 'COD2', NULL, NULL, 'pending', NULL, NULL, NULL, '2026-05-12 05:22:30', '2026-05-12 05:22:30'),
(3, 3, 1, 'bank_transfer', 14999.00, 'ORD3S1', 'https://img.vietqr.io/image/970422-0123456789-compact.png?amount=14999&addInfo=ORD3S1&accountName=NGUYEN%20TUAN', 'ORD3S1', 'pending', NULL, NULL, NULL, '2026-05-12 05:22:55', '2026-05-12 05:22:55'),
(4, 4, 1, 'bank_transfer', 14999.00, 'ORD4S1', 'https://img.vietqr.io/image/970422-0123456789-compact.png?amount=14999&addInfo=ORD4S1&accountName=NGUYEN%20TUAN', 'ORD4S1', 'pending', NULL, NULL, NULL, '2026-05-12 05:26:37', '2026-05-12 05:26:37'),
(5, 6, 9, 'bank_transfer', 13888.00, 'ORD6S9', 'https://img.vietqr.io/image/970422-0868133346-compact.png?amount=13888&addInfo=ORD6S9&accountName=Nguy%E1%BB%85n%20V%C4%83n%20Tr%C6%B0%E1%BB%9Dng', 'ORD6S9', 'paid', 'FT26132601045339', 'NGUYEN VAN TRUONG ORD6S9 FT26132816118001 kC17PEYM/53 1616', '2026-05-12 05:38:39', '2026-05-12 05:34:52', '2026-05-12 05:38:39'),
(6, 7, 9, 'cod', 13888.00, 'COD7', NULL, NULL, 'pending', NULL, NULL, NULL, '2026-05-12 05:40:41', '2026-05-12 05:40:41'),
(7, 8, 9, 'bank_transfer', 13888.00, 'ORD8S9', 'https://img.vietqr.io/image/970422-0868133346-compact.png?amount=13888&addInfo=ORD8S9&accountName=Nguy%E1%BB%85n%20V%C4%83n%20Tr%C6%B0%E1%BB%9Dng', 'ORD8S9', 'paid', 'FT26132728878308', 'NGUYEN VAN TRUONGORD8S9 FT26132406171028 kC17B914/57 8618', '2026-05-12 05:43:07', '2026-05-12 05:40:52', '2026-05-12 05:43:07');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `products`
--

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `price` decimal(15,2) NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `quantity` int(11) DEFAULT 0,
  `category` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `products`
--

INSERT INTO `products` (`id`, `user_id`, `name`, `description`, `price`, `image_url`, `created_at`, `quantity`, `category`) VALUES
(14, 9, 'Đồ da dụng 1', 'Đồ da dụng 1Đồ da dụng 1Đồ da dụng 1', 8888.00, '/static/uploads/download_2.jpg', '2026-05-12 05:34:01', 552, 'Đồ gia dụng');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `seller_bank_configs`
--

CREATE TABLE `seller_bank_configs` (
  `id` int(11) NOT NULL,
  `seller_id` int(11) NOT NULL,
  `bank_name` varchar(100) DEFAULT NULL,
  `bank_acq_id` varchar(20) DEFAULT NULL,
  `account_no` varchar(50) NOT NULL,
  `account_name` varchar(120) NOT NULL,
  `vietqr_client_id` varchar(120) DEFAULT NULL,
  `vietqr_api_key` varchar(255) DEFAULT NULL,
  `bank_history_token` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `seller_bank_configs`
--

INSERT INTO `seller_bank_configs` (`id`, `seller_id`, `bank_name`, `bank_acq_id`, `account_no`, `account_name`, `vietqr_client_id`, `vietqr_api_key`, `bank_history_token`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 1, 'MBBank', '970422', '0123456789', 'NGUYEN TUAN', NULL, NULL, 'e24e44731c4aefcf15f248e5c952953c', 1, '2026-05-12 05:06:24', '2026-05-12 05:29:16'),
(2, 9, 'MBBank', '970422', '0868133346', 'Nguyễn Văn Trường', NULL, NULL, 'e24e44731c4aefcf15f248e5c952953c', 1, '2026-05-12 05:17:40', '2026-05-12 05:17:40');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `full_name` varchar(100) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `role` enum('admin','customer','seller') DEFAULT 'customer',
  `seller_status` enum('pending','approved','rejected') DEFAULT 'approved',
  `shop_name` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `business_type` varchar(100) DEFAULT NULL,
  `shop_description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `full_name`, `created_at`, `role`, `seller_status`, `shop_name`, `phone`, `address`, `business_type`, `shop_description`) VALUES
(1, 'tuannt03', '123', 'Nguyễn Tuấn', '2026-04-03 03:16:17', 'seller', 'approved', 'Nguyễn Tuấn Shop', '0901234567', 'Quan 1, TP. Ho Chi Minh', 'Dien thoai', 'Shop chuyen ban dien thoai va phu kien demo.'),
(2, '1', '1', 'Mary Customer', '2026-04-03 05:24:07', 'customer', 'approved', NULL, NULL, NULL, NULL, NULL),
(3, 'admin', 'admin', 'Admin System', '2026-04-03 06:00:00', 'admin', 'approved', NULL, NULL, NULL, NULL, NULL),
(4, 'shop02', 'scrypt:32768:8:1$80t0EpnrIG0gXcCl$bb25ebe34818ead19b684181528bf7209cdfbc482b53e29b3eedda37c8f15ca39b7c3ec76ec960bd10eca38ac5d78f12aea30f0d5cf63479a08cdaf227c07461', 'Nguyễn Trường', '2026-05-12 05:07:21', 'seller', 'rejected', 's1_shop', '0868133346', 'Xuân Lai , Gia Bình , Bắc Ninh', 'Thoi trang', 'xxxxxxxxxxxxxx'),
(5, 'customer01', 'scrypt:32768:8:1$m1p34h7ZNdWov563$2a7c0f3bde1cb4cd3ecfbffb68da5a46e1ec6db10207ffde20ce276ff4d7c442a4d13ee54bcf497bcf6d61c89037a2ef8aec95fc924b6b5e8c7a7a8bad127de8', 'Nguyễn Trường user 1', '2026-05-12 05:11:18', 'customer', 'approved', NULL, NULL, NULL, NULL, NULL),
(6, 'customer02', 'scrypt:32768:8:1$Nlz3IH9M9BJWjtPc$1d8b9072683e1cd5888213becec7a43ea29bb692bc8755addf030809acbdb50c0aff743adc8d9bccf8ac5d655906e48a716ddcb1729e9f2a8350d3da6c930fd7', 'Nguyen Van Truong', '2026-05-12 05:11:50', 'customer', 'approved', NULL, NULL, NULL, NULL, NULL),
(7, 'seller04', 'scrypt:32768:8:1$bEnHvQ2nhQl6bmnF$fb7b4388edc2fa8182ca9890fc245fcd2d590e584d77e42bb4e17859065bb5e84c633ca6b458727d8eb5d346184e600f53f823ae626c75707080989e93d298d5', 'Nguyễn Trường', '2026-05-12 05:14:04', 'seller', 'rejected', 'seller04', '0868133346', 'Xuân Lai , Gia Bình , Bắc Ninh', 'Thoi trang', 'fsdfsfwef3wrdfdsf'),
(8, 'seller001', 'scrypt:32768:8:1$uHQdCr2SH3X5hKt7$526a32603f59473b51a65d78643efe56e1e8b082c176f28d843055671cbe6e0d41280205a2403d11aeaa6a4644683d866d940ed505aa51e239cf43bfa54a095d', 'seller001', '2026-05-12 05:16:05', 'seller', 'rejected', 'seller001', '0868133346', 'Xuân Lai , Gia Bình , Bắc Ninh', 'Thoi trang', 'xxxxxxxxxxxxxxxxxxxxxxxx'),
(9, 'seller002', 'scrypt:32768:8:1$KhDfEvSKoohuUnR8$e871ca13678a2661fa70a52f79daa7a07de05f4c5da0e6507aa821ccecbd0289aaa1b02e8cb1a39104c61d066bbbcacbb0eda7ca16aab7b053aef0ac01bfe6ab', 'Nguyễn Văn Trường', '2026-05-12 05:16:50', 'seller', 'approved', 'seller002', '0868133346', 'Xuân Lai , Gia Bình , Bắc Ninh', 'Dien thoai', 'seller002seller002');

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `customers`
--
ALTER TABLE `customers`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Chỉ mục cho bảng `orders`
--
ALTER TABLE `orders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `customer_id` (`customer_id`);

--
-- Chỉ mục cho bảng `order_items`
--
ALTER TABLE `order_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `order_id` (`order_id`),
  ADD KEY `product_id` (`product_id`);

--
-- Chỉ mục cho bảng `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `order_id` (`order_id`),
  ADD UNIQUE KEY `payment_code` (`payment_code`),
  ADD KEY `seller_id` (`seller_id`);

--
-- Chỉ mục cho bảng `products`
--
ALTER TABLE `products`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Chỉ mục cho bảng `seller_bank_configs`
--
ALTER TABLE `seller_bank_configs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `seller_id` (`seller_id`);

--
-- Chỉ mục cho bảng `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `shop_name` (`shop_name`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `customers`
--
ALTER TABLE `customers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT cho bảng `orders`
--
ALTER TABLE `orders`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT cho bảng `order_items`
--
ALTER TABLE `order_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT cho bảng `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT cho bảng `products`
--
ALTER TABLE `products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT cho bảng `seller_bank_configs`
--
ALTER TABLE `seller_bank_configs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT cho bảng `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `order_items`
--
ALTER TABLE `order_items`
  ADD CONSTRAINT `fk_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_items_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `fk_payments_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_payments_seller` FOREIGN KEY (`seller_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Các ràng buộc cho bảng `products`
--
ALTER TABLE `products`
  ADD CONSTRAINT `fk_products_seller` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Các ràng buộc cho bảng `seller_bank_configs`
--
ALTER TABLE `seller_bank_configs`
  ADD CONSTRAINT `fk_bank_config_seller` FOREIGN KEY (`seller_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
