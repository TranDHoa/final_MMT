# client.py
import socket
import threading
import sys
import getpass
from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from common import serialize, deserialize

my_name = ""
my_p2p_port = 0
server_conn = None
running = True

active_p2p_conns = {} # { username: socket }
current_chat_target = None # Trạng thái đang chat với ai

def print_ui(msg):
    """In ra Terminal mà không làm đứt đoạn dấu nhắc nhập lệnh"""
    print(f"\r{msg}\n[COMMAND/CHAT] >> ", end="", flush=True)

# --- THREAD 3: P2P LISTENER ---
def p2p_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', my_p2p_port))
    s.listen(5)
    while running:
        try:
            conn, addr = s.accept()
            threading.Thread(target=p2p_receive, args=(conn,), daemon=True).start()
        except:
            break

def p2p_receive(conn):
    buffer = ""
    # Đã sửa: Chuyển vòng lặp ra ngoài try để không bị văng Thread khi 1 tin nhắn lỗi
    while running:
        try:
            raw = conn.recv(BUFFER_SIZE).decode('utf-8')
            if not raw: break
            buffer += raw
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                msg = deserialize(line)
                if msg and msg["type"] == "chat":
                    print_ui(f"[CHAT] {msg['username']} -> You: {msg['payload']}")
        except:
            break
    conn.close()

def connect_p2p(target, ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, int(port)))
        active_p2p_conns[target] = s
        global current_chat_target
        current_chat_target = target
        print_ui(f"[SYSTEM] Đã kết nối với {target}. Bạn có thể bắt đầu chat trực tiếp.")
    except Exception as e:
        print_ui(f"[ERROR] Không thể kết nối tới {target}: {e}")

# --- THREAD 1: SERVER LISTENER ---
def receive_from_server():
    global running
    buffer = ""
    while running:
        try:
            raw = server_conn.recv(BUFFER_SIZE).decode('utf-8')
            if not raw: break
            buffer += raw
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                msg = deserialize(line)
                if not msg: continue
                
                m_type = msg["type"]
                
                # 1. XỬ LÝ RESPONSE ĐĂNG NHẬP
                if m_type == "sign_in_response":
                    res = msg["payload"]
                    if res["status"] == "fail":
                        print(f"\n[LỖI] {res['reason']}")
                        running = False
                        server_conn.close()
                    else:
                        print_ui("[HỆ THỐNG] Xác thực thành công!")

                # 2. XỬ LÝ PING TỪ SERVER
                elif m_type == "keep_alive":
                    #pass
                    server_conn.sendall(serialize("keep_alive_ack", my_name).encode('utf-8'))
                
                # 3. XỬ LÝ THÔNG BÁO ONLINE / OFFLINE TỪ SERVER
                elif m_type == "status_update":
                    print_ui(msg["payload"])
                
                # 4. XỬ LÝ DANH SÁCH USER ĐANG ONLINE (Khi vừa đăng nhập)
                elif m_type == "client_status":
                    print_ui(f"[DANH SÁCH ONLINE] {msg['payload']}")
                
                # 5. XỬ LÝ KẾT QUẢ TÌM KIẾM ĐỂ CHAT P2P
                elif m_type == "chat_res":
                    target = msg["payload"]
                    target_ip = msg.get("ip")
                    target_port = msg.get("port")
                    connect_p2p(target, target_ip, target_port)
                
                # 6. XỬ LÝ LỖI (VD: User không tồn tại)
                elif m_type == "error":
                    print_ui(f"[LỖI] {msg['payload']}")
                
        except Exception as e:
            if running:
                print_ui(f"[!] Mất kết nối tới máy chủ trung tâm: {e}")
                running = False
            break

def main():
    global my_name, my_p2p_port, server_conn, running, current_chat_target
    
    # Validation logic 
    while True:
        my_name = input("Nhập username (viết liền): ").strip()
        if my_name and " " not in my_name: break
        print("[!] Username không hợp lệ.")
        
    my_password = getpass.getpass("Nhập password (ký tự sẽ bị ẩn): ")
    my_p2p_port = int(input("Nhập cổng P2P (VD: 5001): "))

    threading.Thread(target=p2p_listener, daemon=True).start()

    server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_conn.connect((SERVER_HOST, SERVER_PORT))
    except:
        print("Không thể kết nối Server!")
        return

    threading.Thread(target=receive_from_server, daemon=True).start()

    # Gửi Sign In KÈM PASSWORD
    server_conn.sendall(serialize("sign_in", my_name, ip="127.0.0.1", port=my_p2p_port, password=my_password).encode('utf-8'))

    # Chờ 0.5s để xem có bị server kick vì sai pass không trước khi in UI chat
    import time; time.sleep(0.5)
    if not running: sys.exit()
    
    print("\n--- HỆ THỐNG CHAT P2P ---")
    print("Lệnh: /chat <username> | /exit")
    print("-------------------------\n")

    while running:
        try:
            cmd = input("[COMMAND/CHAT] >> ")
            if not cmd: continue
            
            if cmd == "/exit":
                server_conn.sendall(serialize("sign_out", my_name).encode('utf-8'))
                running = False
                break
                
            elif cmd.startswith("/chat "):
                # Gửi yêu cầu xin IP/Port của người muốn chat lên Server
                target = cmd.split(" ")[1]
                server_conn.sendall(serialize("chat_req", my_name, payload=target).encode('utf-8'))
                
            else:
                # Nếu không phải lệnh, gửi tin nhắn đến target hiện tại
                if current_chat_target and current_chat_target in active_p2p_conns:
                    msg = serialize("chat", my_name, payload=cmd)
                    active_p2p_conns[current_chat_target].sendall(msg.encode('utf-8'))
                    print_ui(f"[CHAT] You -> {current_chat_target}: {cmd}")
                else:
                    print_ui("[!] Bạn chưa chọn người chat. Hãy dùng lệnh: /chat <username>")
                    
        except KeyboardInterrupt:
            server_conn.sendall(serialize("sign_out", my_name).encode('utf-8'))
            running = False
            break

    server_conn.close()
    sys.exit()

if __name__ == "__main__":
    main()