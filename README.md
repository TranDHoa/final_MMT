## 🚀 Quy Trình Khởi Chạy Hệ Thống Kiểm Thử

Để kiểm thử kịch bản hoạt động đa người dùng trên cùng một máy nội bộ (`127.0.0.1`), hãy thực hiện tuần tự các bước sau:

### Bước 1: Khởi động Máy chủ trung tâm (Server)

Mở một cửa sổ Terminal mới và chạy lệnh:

```bash
python server.py

```

* Sau khi chạy, Server sẽ lắng nghe tại cổng mặc định `9999`.
* Hệ thống sẽ tự động khởi tạo các file cơ sở dữ liệu: `accounts.csv` (chứa tài khoản mẫu), `users.csv` (theo dõi trạng thái) và `logs.csv`.

### Bước 2: Khởi chạy Client thứ nhất (Tài khoản Hoa)

Mở một cửa sổ Terminal độc lập thứ hai, chạy lệnh:

```bash
python main.py

```

* Form đăng nhập hiện lên, ô nhập Port đã được ẩn tự động hóa.
* Nhập tài khoản: **Username:** `Hoa` | **Password:** `123456`.
* Bấm **Login**. Hệ thống tự động cấp cổng và chuyển vào màn hình Chat. Trên danh sách `ONLINE` bên trái sẽ hiển thị tên của Hoa cùng địa chỉ mạng.

### Bước 3: Khởi chạy Client thứ hai (Tài khoản Bình)

Mở tiếp một cửa sổ Terminal độc lập thứ ba, chạy lệnh:

```bash
python main.py

```

* Nhập tài khoản: **Username:** `Binh` | **Password:** `abc123`.
* Bấm **Login**. Hệ thống tự động chuyển vào màn hình Chat.
* Ngay lập tức, cả hai màn hình của Hoa và Bình đều tự động cập nhật danh sách hiển thị tên của nhau nhờ cơ chế Signaling Broadcast từ Server.

### Bước 4: Tiến hành Chat P2P trực tiếp

1. Từ màn hình của Hoa, hãy **nhấp đúp chuột** vào tên `Binh` trong danh sách `ONLINE` bên trái.
2. Hệ thống sẽ hiển thị dòng chữ màu xanh: `[!] Đã kết nối P2P với Binh. Bạn có thể bắt đầu nhắn tin.`
3. Nhập tin nhắn vào ô chữ phía dưới và nhấn **Enter** hoặc bấm nút **Send**. Tin nhắn sẽ truyền thẳng tới màn hình của Bình mà hoàn toàn không đi qua Server.

---

## 🧪 Các Kịch Bản Kiểm Thử Cần Thực Hiện (Test Cases)

Hệ thống đã được thiết kế tối ưu để vượt qua các bộ test case cốt lõi sau:

### 1. Nhóm Đăng nhập & Xác thực

* **TC-AUTH-01 (Đăng nhập thành công):** Điền đúng thông tin tài khoản mẫu, hệ thống truy cập mượt mà.
* **TC-AUTH-02 (Kiểm tra bỏ trống):** Để trống trường thông tin, ứng dụng hiển thị hộp thoại thông báo yêu cầu nhập đủ.
* **TC-AUTH-03 (Chống Brute-force):** Điền sai mật khẩu 3 lần liên tiếp, tài khoản bị khóa tạm thời, hệ thống từ chối đăng nhập ở lần thứ 4 cho đến khi Server reset.
* **TC-AUTH-04 (Chống Đăng nhập trùng):** Nếu tài khoản `Hoa` đang online, một máy khác cố tình đăng nhập tài khoản `Hoa` sẽ bị Server từ chối để bảo vệ phiên kết nối.

### 2. Nhóm Heartbeat & Đồng bộ Trạng thái

* **TC-SESS-01 (Giám sát Keep-Alive):** Khi Client giữ kết nối, kiểm tra Terminal của Server sẽ liên tục in log dạng:
```plaintext
[KEEP-ALIVE] Đã gửi Ping tới -> Hoa
[KEEP-ALIVE] Đã nhận ACK từ <- Hoa

```


* **TC-SESS-02 (Đăng xuất chủ động):** Bấm nút `X` tắt cửa sổ chat, Client lập tức gửi gói tin `sign_out`, Server xóa session và cập nhật danh sách offline cho các máy còn lại ngay lập tức.
* **TC-SESS-03 (Xử lý mất mạng/Đột ngột tắt ứng dụng):** Tắt đột ngột app (bằng cách tắt Terminal client). Sau 15 giây không nhận được phản hồi ACK, Server tự động kích hoạt bộ đếm Timeout, ngắt kết nối và giải phóng tài nguyên.

### 3. Nhóm Truyền tải dữ liệu P2P

* **TC-P2P-01 (Chống tự chat):** Nhấp đúp vào chính tên mình trong danh sách online, hệ thống hiển thị thông báo ngăn chặn hành vi.
* **TC-P2P-02 (Xử lý ngắt P2P cô lập):** Khi Hoa và Bình đang chat P2P, nếu Bình tắt ứng dụng, Hoa gửi tin nhắn tiếp theo sẽ nhận được thông báo lỗi cô lập luồng socket thay vì làm sập toàn bộ ứng dụng (`main.py` vẫn giữ nguyên hoạt động).

---

## 📊 Công cụ kiểm tra dữ liệu ngầm trên Server

Tại cửa sổ Terminal của Server, bạn có thể gõ lệnh trực tiếp sau để kiểm tra trạng thái lưu trữ của file CSV trong bộ nhớ đệm:

```bash
/show_db

```

Màn hình sẽ hiển thị bảng dữ liệu trực quan:

```plaintext
=================================================================
USERNAME        | IP              | PORT   | STATUS   | LAST_SEEN
-----------------------------------------------------------------
Hoa             | 127.0.0.1       | 51234  | online   | 2026-06-10 00:45:12
Binh            | 127.0.0.1       | 51238  | online   | 2026-06-10 00:45:15
=================================================================

```
