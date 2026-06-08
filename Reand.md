# 🧪 KỊCH BẢN TEST END-TO-END HỆ THỐNG CHAT CLIENT-SERVER

## 📌 Test 1: Khởi động Server và nạp Database

### Bước 1:

Tại Terminal 1, chạy lệnh:

```bash
python server.py
```

### ✅ Kết quả mong đợi:

* Server in ra:

  * `[AUTH] Đã tạo database xác thực...` *(nếu chạy lần đầu)*
  * `[DB] Hệ thống CSDL đã sẵn sàng. Đã reset toàn bộ user về OFFLINE.`
  * `=== SERVER CHẠY TẠI 127.0.0.1:9999 ===`

---

## 📌 Test 2: Đăng nhập thành công (Valid Login)

### Bước 1:

Tại Terminal 2:

```bash
python client.py
```

### Bước 2: Nhập thông tin

```
Username: A
Password: 123456
Port: 5001
```

### ✅ Kết quả mong đợi:

* Client:

  * `[HỆ THỐNG] Xác thực thành công!`
  * Hiển thị giao diện chat

* Server log:

  * `[AUTH] A login SUCCESS`
  * `[CONNECT] A connected`

---

## 📌 Test 3: Sai Password & Khóa tài khoản (Brute-force limit)

### Bước 1:

Tại Terminal 3:

```bash
python client.py
```

### Bước 2: Nhập sai thông tin

```
Username: B
Password: sai_mat_khau
Port: 5002
```

### ✅ Kết quả mong đợi (Lần 1 & 2):

* Client:

  * `[LỖI] Sai mật khẩu. Bạn còn x lần thử.`
* Server:

  * `[AUTH] B login FAIL (Sai mật khẩu...)`

### Bước 3:

Nhập sai đến lần thứ 3

### ✅ Kết quả mong đợi (Lần 3):

* Client:

  * `[LỖI] Tài khoản đã bị khóa do nhập sai quá 3 lần.`

📌 **Lưu ý:**
Cơ chế khóa lưu trên RAM → restart server sẽ reset.

---


## 📌 Test 5: Chat P2P & cập nhật trạng thái Real-time

### Bước 1:

Đăng nhập user C:

```
Username: C
Password: pass123
Port: 5003
```

### Bước 2:

* Client A nhận:

  * `[UPDATE] [+] C vừa online`

### Bước 3:

Tại Client A:

```bash
/chat C
Xin chao C, toi la A day!
```

### ✅ Kết quả mong đợi:

* Client C:

  * `[CHAT] A -> You: Xin chao C, toi la A day!`
* Server:

  * ❌ Không in nội dung tin nhắn

---

## 📌 Test 6: Kiểm tra Database

### Bước 1:

Tại Server:

```bash
/show_db
```

### ✅ Kết quả mong đợi:

* User A: `online`
* User C: `online`
* User B: `offline`

---

### Bước 2:

Mở file:

```
logs.csv
```

### ✅ Kết quả mong đợi:

* Log thời gian `sign_in` của A và C
* ❌ Không ghi login thất bại

📌 **Lưu ý:**
Không mở bằng Excel (tránh lỗi Permission) → dùng Notepad hoặc VS Code.

---

## 📌 Test 7: Đăng xuất & Timeout

### Bước 1:
Tại file client.py sửa 
elif m_type == "keep_alive":
    #pass
    server_conn.sendall(serialize("keep_alive_ack", my_name).encode('utf-8'))

-> thành:
elif m_type == "keep_alive":
    pass
    #server_conn.sendall(serialize("keep_alive_ack", my_name).encode('utf-8'))

Tại Client A:

```bash
/exit
```

### ✅ Kết quả mong đợi:

* Client A thoát
* Client C nhận:

  * `[UPDATE] [-] A đã offline`
* Server cập nhật DB + log

---

### Bước 2:

Tắt ngang Client C (bấm ❌)

### ✅ Kết quả mong đợi:

* Server gửi keep-alive
* Sau ~15s:

  * `[TIMEOUT] remove C`
* DB cập nhật `offline`
* Log:

  * `unexpected_disconnect`

---

# ✅ Tổng kết

Hệ thống đã được test đầy đủ các chức năng:

* Authentication (Login/Fail/Lock)
* Session management
* Duplicate login prevention
* Real-time status update
* P2P messaging
* Database + logging
* Timeout handling

---

🚀 **Sẵn sàng deploy hoặc nâng cấp thêm (GUI, mã hóa, scaling server, etc.)**
