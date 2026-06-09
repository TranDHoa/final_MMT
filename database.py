# database.py
import csv
import os
from datetime import datetime
import threading

USERS_FILE = 'users.csv'
LOGS_FILE = 'logs.csv'
db_lock = threading.Lock()

def _get_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_db():
    with db_lock:
        if not os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "username", "action", "ip"])

        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, mode='r', newline='', encoding='utf-8') as f:
                users = list(csv.DictReader(f))

        with open(USERS_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "ip", "port", "status", "last_seen"])
            writer.writeheader()
            for u in users:
                u['status'] = 'offline'
                writer.writerow(u)
        print("[DB] Hệ thống CSDL đã sẵn sàng.")

def log_event(username, action, ip):
    with db_lock:
        with open(LOGS_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([_get_now(), username, action, ip])

def update_user_status(username, ip, port, status):
    """Hàm gộp chung để xử lý online/offline/last_seen cho tối ưu"""
    with db_lock:
        users = []
        found = False
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, mode='r', newline='', encoding='utf-8') as f:
                users = list(csv.DictReader(f))
                
        for u in users:
            if u['username'] == username:
                if ip is not None: u['ip'] = str(ip)
                if port is not None: u['port'] = str(port)
                u['status'] = status
                u['last_seen'] = _get_now()
                found = True
                break
                
        if not found and status == 'online':
            users.append({
                "username": username, "ip": str(ip), "port": str(port),
                "status": "online", "last_seen": _get_now()
            })
            
        with open(USERS_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "ip", "port", "status", "last_seen"])
            writer.writeheader()
            writer.writerows(users)

def show_database():
    with db_lock:
        if not os.path.exists(USERS_FILE): return
        with open(USERS_FILE, mode='r', newline='', encoding='utf-8') as f:
            users = list(csv.DictReader(f))
        print("\n" + "="*65)
        print(f"{'USERNAME':<15} | {'IP':<15} | {'PORT':<6} | {'STATUS':<8} | {'LAST_SEEN'}")
        print("-" * 65)
        for u in users:
            print(f"{u['username']:<15} | {u['ip']:<15} | {u['port']:<6} | {u['status']:<8} | {u['last_seen']}")
        print("="*65 + "\n")