🚀 Hệ Thống Chat Client-Server với P2P Messaging
📌 Giới thiệu

Đây là hệ thống chat hoạt động theo mô hình Client-Server kết hợp P2P (Peer-to-Peer).
Server chịu trách nhiệm xác thực, quản lý trạng thái người dùng và signaling, trong khi dữ liệu chat được truyền trực tiếp giữa các client.

⚙️ Kiến trúc hệ thống
Server (server.py)
Xác thực tài khoản
Quản lý trạng thái ONLINE/OFFLINE
Gửi danh sách user online (broadcast)
Giám sát kết nối (Keep-alive / Heartbeat)
Client (main.py)
Giao diện đăng nhập & chat
Kết nối server để xác thực
Thiết lập kết nối P2P với client khác
Gửi/nhận tin nhắn trực tiếp
🧱 Cơ sở dữ liệu (CSV)

Hệ thống sử dụng file CSV đơn giản:

accounts.csv → lưu tài khoản mẫu
users.csv → trạng thái người dùng
logs.csv → log hoạt động hệ thống
🚀 Hướng dẫn khởi chạy hệ thống
🔹 Bước 1: Khởi động Server
python server.py
Server chạy tại: 127.0.0.1:9999
Tự động tạo database nếu chưa tồn tại
🔹 Bước 2: Khởi chạy Client 1 (Hoa)
python main.py

Thông tin đăng nhập:

Username: Hoa
Password: 123456
🔹 Bước 3: Khởi chạy Client 2 (Bình)
python main.py

Thông tin đăng nhập:

Username: Binh
Password: abc123
🔹 Bước 4: Chat P2P
Nhấp đúp vào user trong danh sách ONLINE
Hệ thống hiển thị:
[!] Đã kết nối P2P với <username>
Tin nhắn được gửi trực tiếp (không qua server)
🧪 Test Cases
🔐 1. Authentication
TC-AUTH-01: Đăng nhập đúng → Thành công
TC-AUTH-02: Bỏ trống → Hiển thị cảnh báo
TC-AUTH-03: Sai 3 lần → Khóa tài khoản tạm thời
TC-AUTH-04: Login trùng → Bị từ chối
🔄 2. Session & Heartbeat
TC-SESS-01: Keep-alive hoạt động
[KEEP-ALIVE] Ping -> Hoa
[KEEP-ALIVE] ACK <- Hoa
TC-SESS-02: Đóng app → logout ngay
TC-SESS-03: Mất kết nối → timeout sau 15s
💬 3. P2P Messaging
TC-P2P-01: Không cho self-chat
TC-P2P-02: Client mất kết nối → không crash app
📊 Debug & Monitoring

Trên server terminal:

/show_db

Hiển thị:

USERNAME | IP         | PORT  | STATUS | LAST_SEEN
-------------------------------------------------
Hoa      | 127.0.0.1 | 51234 | online | ...
Binh     | 127.0.0.1 | 51238 | online | ...
