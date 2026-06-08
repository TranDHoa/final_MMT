# database.py
import csv
import os
from datetime import datetime
import threading

USERS_FILE = 'users.csv'
LOGS_FILE = 'logs.csv'

# Khóa (Lock) để đảm bảo tại một thời điểm chỉ có 1 luồng (thread) được quyền ghi file
db_lock = threading.Lock()

def _get_now():
    """Hàm phụ trợ lấy thời gian hiện tại"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_db():
    """Khởi tạo database khi server start. Tự tạo file nếu chưa có và reset online status."""
    with db_lock:
        # 1. Tạo file logs nếu chưa có
        if not os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "username", "action", "ip"])

        # 2. Đọc file users hiện tại (nếu có)
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                users = list(reader)

        # 3. Ghi đè file users, reset toàn bộ về trạng thái 'offline'
        with open(USERS_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "ip", "port", "status", "last_seen"])
            writer.writeheader()
            for u in users:
                u['status'] = 'offline'
                writer.writerow(u)
                
        print("[DB] Hệ thống CSDL đã sẵn sàng. Đã reset toàn bộ user về OFFLINE.")

def log_event(username, action, ip):
    """Ghi lịch sử vào logs.csv"""
    with db_lock:
        with open(LOGS_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([_get_now(), username, action, ip])
        print(f"[DB] Log saved: {action} ({username})")

def _read_users():
    """Hàm phụ trợ đọc danh sách users (Chỉ gọi bên trong khối with db_lock)"""
    if not os.path.exists(USERS_FILE): return []
    with open(USERS_FILE, mode='r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def _write_users(users):
    """Hàm phụ trợ ghi danh sách users (Chỉ gọi bên trong khối with db_lock)"""
    with open(USERS_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["username", "ip", "port", "status", "last_seen"])
        writer.writeheader()
        writer.writerows(users)

def add_or_update_user(username, ip, port):
    """Thêm user mới hoặc cập nhật user cũ khi họ Sign In"""
    with db_lock:
        users = _read_users()
        found = False
        for u in users:
            if u['username'] == username:
                u['ip'] = str(ip)
                u['port'] = str(port)
                u['status'] = 'online'
                u['last_seen'] = _get_now()
                found = True
                break
                
        if not found:
            users.append({
                "username": username, "ip": str(ip), "port": str(port),
                "status": "online", "last_seen": _get_now()
            })
            
        _write_users(users)
        print(f"[DB] User {username} -> ONLINE")

def set_user_offline(username):
    """Đổi trạng thái user thành offline khi Sign Out hoặc Timeout"""
    with db_lock:
        users = _read_users()
        for u in users:
            if u['username'] == username:
                u['status'] = 'offline'
                u['last_seen'] = _get_now()
                break
        _write_users(users)
        print(f"[DB] User {username} -> OFFLINE")

def update_last_seen(username):
    """Cập nhật thời gian hoạt động cuối cùng khi nhận được Keep_Alive_Ack"""
    with db_lock:
        users = _read_users()
        for u in users:
            if u['username'] == username:
                u['last_seen'] = _get_now()
                break
        _write_users(users)

def show_database():
    """In danh sách database ra Terminal cho mục đích Debug"""
    with db_lock:
        users = _read_users()
        print("\n" + "="*65)
        print(f"{'USERNAME':<15} | {'IP':<15} | {'PORT':<6} | {'STATUS':<8} | {'LAST_SEEN'}")
        print("-" * 65)
        for u in users:
            print(f"{u['username']:<15} | {u['ip']:<15} | {u['port']:<6} | {u['status']:<8} | {u['last_seen']}")
        print("="*65 + "\n")