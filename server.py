# server.py
import socket
import threading
import time
from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE, HEARTBEAT_INTERVAL, TIMEOUT_LIMIT
from common import serialize, deserialize
import database as db 
import auth

clients = {}
clients_lock = threading.Lock()

def broadcast(msg, exclude_conn=None):
    encoded_msg = msg.encode('utf-8')
    # VÁ LỖI: Chỉ dùng Lock để copy danh sách kết nối, tránh làm nghẽn toàn bộ server
    with clients_lock:
        target_conns = [info["conn"] for info in clients.values() if info["conn"] != exclude_conn]
        
    for conn in target_conns:
        try:
            conn.sendall(encoded_msg)
        except:
            pass

def heartbeat_manager():
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        to_remove = []
        
        with clients_lock:
            for user, info in clients.items():
                if time.time() - info["last_seen"] > TIMEOUT_LIMIT:
                    to_remove.append((user, info["ip"])) # Lưu IP để log
                else:
                    try:
                        info["conn"].sendall(serialize("keep_alive", "SERVER").encode('utf-8'))
                        print(f"[KEEP-ALIVE] Đã gửi Ping tới -> {user}") # HIỂN THỊ LOG GỬI
                    except:
                        to_remove.append((user, info["ip"]))
        
        for user, ip in to_remove:
            print(f"[TIMEOUT] remove {user}")
            with clients_lock:
                if user in clients:
                    clients[user]["conn"].close()
                    clients.pop(user)
                    
            # --- CẬP NHẬT DATABASE ---
            db.set_user_offline(user)
            db.log_event(user, "timeout_disconnect", ip)
            # -------------------------
            
            broadcast(serialize("status_update", "SERVER", payload=f"[-] {user} đã offline (timeout)"))

def handle_client(conn, addr):
    username = None
    ip = addr[0]
    m_type = None # VÁ LỖI: Khởi tạo biến mặc định để tránh lỗi UnboundLocalError khi client rớt mạng sớm
    buffer = ""
    try:
        while True:
            raw = conn.recv(BUFFER_SIZE).decode('utf-8')
            if not raw: break
            
            buffer += raw
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                msg = deserialize(line)
                if not msg: continue
                
                m_type = msg["type"]
                user = msg.get("username", "")

                if m_type == "sign_in":
                    password = msg.get("password", "")
                    
                    # 1. KIỂM TRA XÁC THỰC TỪ AUTH.PY
                    is_valid, reason = auth.check_login(user, password)
                    
                    if not is_valid:
                        print(f"[AUTH] {user} login FAIL ({reason})")
                        response = {"status": "fail", "reason": reason}
                        conn.sendall(serialize("sign_in_response", "SERVER", payload=response).encode('utf-8'))
                        return # Từ chối và ngắt kết nối ngay lập tức

                    # 2. KIỂM TRA ĐĂNG NHẬP TRÙNG
                    with clients_lock:
                        if user in clients:
                            print(f"[AUTH] {user} login FAIL (Đang online nơi khác)")
                            response = {"status": "fail", "reason": "Tài khoản đang online ở một thiết bị khác!"}
                            conn.sendall(serialize("sign_in_response", "SERVER", payload=response).encode('utf-8'))
                            return
                        
                        # 3. NẾU VƯỢ QUA HẾT -> CHO PHÉP LOGIN
                        clients[user] = {
                            "conn": conn,
                            "ip": msg["ip"],
                            "port": msg["port"],
                            "last_seen": time.time()
                        }
                    
                    username = user
                    print(f"[AUTH] {username} login SUCCESS")
                    
                    # Gửi response thành công cho Client
                    conn.sendall(serialize("sign_in_response", "SERVER", payload={"status": "success"}).encode('utf-8'))
                    
                    # Cập nhật Database trạng thái
                    db.add_or_update_user(username, msg["ip"], msg["port"])
                    db.log_event(username, "sign_in", msg["ip"])
                    
                    print(f"[CONNECT] {username} connected")
                    online_users = [f"{k} ({v['ip']}:{v['port']})" for k, v in clients.items()]
                    conn.sendall(serialize("client_status", "SERVER", payload=",".join(online_users)).encode('utf-8'))
                    broadcast(serialize("status_update", "SERVER", payload=f"[+] {username} vừa online"), exclude_conn=conn)
                    
                elif m_type == "keep_alive_ack":
                    print(f"[KEEP-ALIVE] Đã nhận ACK từ <- {username}") # HIỂN THỊ LOG NHẬN
                    with clients_lock:
                        if username in clients:
                            clients[username]["last_seen"] = time.time()
                    
                    # --- CẬP NHẬT DATABASE ---
                    db.update_last_seen(username)
                    # -------------------------

                elif m_type == "chat_req":
                    target = msg["payload"]
                    with clients_lock:
                        if target in clients:
                            t_info = clients[target]
                            conn.sendall(serialize("chat_res", "SERVER", ip=t_info["ip"], port=t_info["port"], payload=target).encode('utf-8'))
                        else:
                            conn.sendall(serialize("error", "SERVER", payload=f"Không tìm thấy {target}").encode('utf-8'))

                elif m_type == "sign_out":
                    print(f"[DISCONNECT] {username} signed out")
                    return # Kích hoạt khối finally bên dưới

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        if username:
            with clients_lock:
                if username in clients:
                    ip = clients[username]["ip"] # Lấy lại IP trước khi xoá
                    clients.pop(username)
            
            # --- CẬP NHẬT DATABASE ---
            db.set_user_offline(username)
            db.log_event(username, "sign_out" if m_type == "sign_out" else "unexpected_disconnect", ip)
            # -------------------------
            
            broadcast(serialize("status_update", "SERVER", payload=f"[-] {username} đã offline"))
        conn.close()

def server_console():
    """Luồng xử lý lệnh gõ vào cửa sổ Terminal của Server"""
    while True:
        try:
            cmd = input()
            if cmd == "/show_db":
                db.show_database()
        except EOFError:
            break

def main():
    # Khởi tạo DB (reset online status, tạo file nếu thiếu)
    db.init_db()
    auth.init_auth_db()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    
    print(f"=== SERVER CHẠY TẠI {SERVER_HOST}:{SERVER_PORT} ===")
    print("Gõ lệnh '/show_db' để xem Database In-Memory hiện tại.\n")
    
    # Chạy luồng Heartbeat
    threading.Thread(target=heartbeat_manager, daemon=True).start()
    
    # Chạy luồng Server Console Input
    threading.Thread(target=server_console, daemon=True).start()
    
    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()