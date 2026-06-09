# auth.py
import csv
import os

AUTH_FILE = 'accounts.csv'
MAX_FAILED_ATTEMPTS = 3

failed_attempts = {}

def init_auth_db():
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password'])
            writer.writerow(['Hoa', '123456'])
            writer.writerow(['Binh', 'abc123'])
            writer.writerow(['Thanh', 'pass123'])
        print(f"[AUTH] Đã tạo database xác thực: {AUTH_FILE}")

def load_users():
    users = {}
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users[row['username']] = row['password']
    return users

def check_login(username, password):
    if failed_attempts.get(username, 0) >= MAX_FAILED_ATTEMPTS:
        return False, "Tài khoản đã bị khóa do nhập sai quá 3 lần."

    users = load_users()
    if username not in users:
        return False, "Username không tồn tại trong hệ thống."

    if users[username] == password:
        if username in failed_attempts:
            del failed_attempts[username]
        return True, "Thành công"
    else:
        failed_attempts[username] = failed_attempts.get(username, 0) + 1
        remains = MAX_FAILED_ATTEMPTS - failed_attempts[username]
        return False, f"Sai mật khẩu. Bạn còn {remains} lần thử."