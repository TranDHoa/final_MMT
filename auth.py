import csv
import os

AUTH_FILE = 'accounts.csv'
MAX_FAILED_ATTEMPTS = 3

# Lưu trữ số lần đăng nhập sai: { username: số_lần }
failed_attempts = {}

def init_auth_db():
    """Tạo file accounts.csv với một số tài khoản mẫu nếu file chưa tồn tại"""
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password'])
            # Ghi tài khoản mẫu với mật khẩu dạng plaintext (chữ thường)
            writer.writerow(['Hoa', '123456'])
            writer.writerow(['Binh', 'abc123'])
            writer.writerow(['Thanh', 'pass123'])
        print(f"[AUTH] Đã tạo database xác thực: {AUTH_FILE}")

def load_users():
    """Đọc toàn bộ tài khoản từ file CSV vào Dictionary"""
    users = {}
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users[row['username']] = row['password']
    return users

def check_login(username, password):
    """
    Kiểm tra logic đăng nhập.
    Trả về Tuple: (Boolean_Trạng_thái, String_Lý_do)
    """
    # 1. Kiểm tra tài khoản có bị khóa tạm thời không
    if failed_attempts.get(username, 0) >= MAX_FAILED_ATTEMPTS:
        return False, "Tài khoản đã bị khóa do nhập sai quá 3 lần."

    users = load_users()
    
    # 2. Kiểm tra Username tồn tại
    if username not in users:
        return False, "Username không tồn tại trong hệ thống."

    # 3. So sánh trực tiếp mật khẩu (Plaintext)
    if users[username] == password:
        # Nếu đăng nhập đúng -> Xóa lịch sử nhập sai
        if username in failed_attempts:
            del failed_attempts[username]
        return True, "Thành công"
    else:
        # Nếu đăng nhập sai -> Tăng biến đếm
        failed_attempts[username] = failed_attempts.get(username, 0) + 1
        remains = MAX_FAILED_ATTEMPTS - failed_attempts[username]
        return False, f"Sai mật khẩu. Bạn còn {remains} lần thử."