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
    with clients_lock:
        target_conns = [info["conn"] for info in clients.values() if info["conn"] != exclude_conn]
    for conn in target_conns:
        try:
            conn.sendall(encoded_msg)
        except: pass

def broadcast_online_list():
    """Hàm mới: Gửi danh sách user đang online cho TẤT CẢ mọi người"""
    with clients_lock:
        online_users = [f"{k} ({v['ip']}:{v['port']})" for k, v in clients.items()]
    list_str = ",".join(online_users) if online_users else ""
    broadcast(serialize("client_status", "SERVER", payload=list_str))

def heartbeat_manager():
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        to_remove = []
        with clients_lock:
            for user, info in clients.items():
                if time.time() - info["last_seen"] > TIMEOUT_LIMIT:
                    to_remove.append((user, info["ip"]))
                else:
                    try:
                        info["conn"].sendall(serialize("keep_alive", "SERVER").encode('utf-8'))
                        print(f"[KEEP-ALIVE] Đã gửi Ping tới -> {user}")
                    except:
                        to_remove.append((user, info["ip"]))
        
        for user, ip in to_remove:
            with clients_lock:
                if user in clients:
                    try:
                        clients[user]["conn"].close()
                    except: pass
                    clients.pop(user)
            db.update_user_status(user, None, None, 'offline')
            db.log_event(user, "timeout_disconnect", ip)
            broadcast(serialize("status_update", "SERVER", payload=f"[-] {user} đã offline (timeout)"))
            
            # Cập nhật danh sách mới cho những người còn lại
            broadcast_online_list() 

def handle_client(conn, addr):
    username = None
    ip = addr[0]
    m_type = None
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
                    is_valid, reason = auth.check_login(user, password)
                    if not is_valid:
                        conn.sendall(serialize("sign_in_response", "SERVER", payload={"status": "fail", "reason": reason}).encode('utf-8'))
                        return

                    with clients_lock:
                        if user in clients:
                            conn.sendall(serialize("sign_in_response", "SERVER", payload={"status": "fail", "reason": "Tài khoản đang online nơi khác!"}).encode('utf-8'))
                            return
                        clients[user] = {"conn": conn, "ip": msg["ip"], "port": msg["port"], "last_seen": time.time()}
                    
                    username = user
                    conn.sendall(serialize("sign_in_response", "SERVER", payload={"status": "success"}).encode('utf-8'))
                    
                    db.update_user_status(username, msg["ip"], msg["port"], 'online')
                    db.log_event(username, "sign_in", msg["ip"])
                    
                    broadcast(serialize("status_update", "SERVER", payload=f"[+] {username} vừa online"), exclude_conn=conn)
                    
                    # Gửi danh sách mới cho toàn mạng (bao gồm cả người vừa đăng nhập)
                    broadcast_online_list() 
                    
                elif m_type == "keep_alive_ack":
                    print(f"[KEEP-ALIVE] Đã nhận ACK từ <- {username}")
                    with clients_lock:
                        if username in clients:
                            clients[username]["last_seen"] = time.time()
                    db.update_user_status(username, None, None, 'online')

                elif m_type == "chat_req":
                    target = msg["payload"]
                    with clients_lock:
                        if target in clients:
                            t_info = clients[target]
                            conn.sendall(serialize("chat_res", "SERVER", ip=t_info["ip"], port=t_info["port"], payload=target).encode('utf-8'))
                        else:
                            conn.sendall(serialize("error", "SERVER", payload=f"Không tìm thấy {target}").encode('utf-8'))

                elif m_type == "sign_out":
                    return

    except Exception as e:
        pass
    finally:
        if username:
            with clients_lock:
                if username in clients:
                    ip = clients[username]["ip"]
                    clients.pop(username)
            db.update_user_status(username, None, None, 'offline')
            db.log_event(username, "sign_out" if m_type == "sign_out" else "unexpected_disconnect", ip)
            broadcast(serialize("status_update", "SERVER", payload=f"[-] {username} đã offline"))
            
            # Cập nhật danh sách mới khi có người thoat
            broadcast_online_list() 
        conn.close()

def server_console():
    while True:
        try:
            cmd = input()
            if cmd == "/show_db": db.show_database()
        except EOFError: break

def main():
    db.init_db()
    auth.init_auth_db()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"=== SERVER RUNNING AT {SERVER_HOST}:{SERVER_PORT} ===")
    
    threading.Thread(target=heartbeat_manager, daemon=True).start()
    threading.Thread(target=server_console, daemon=True).start()
    
    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()