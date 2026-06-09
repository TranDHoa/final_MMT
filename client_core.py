# client_core.py
import socket
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from common import serialize, deserialize
from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE

class NetworkManager(QThread):
    login_result = pyqtSignal(bool, str) 
    system_msg = pyqtSignal(str)         
    chat_ready = pyqtSignal(str, str, str) 
    receive_msg = pyqtSignal(str, str)   
    
    # Tín hiệu mới chuyên dụng cho danh sách online
    update_online_list = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        self.username = ""
        self.p2p_port = 0
        self.server_conn = None
        self.running = False
        self.p2p_conns = {} 
        self.last_online_list = "" # Biến lưu đệm chống Race Condition
        
    def connect_and_login(self, username, password):
        self.username = username
        
        # [THÊM MỚI] Yêu cầu Hệ điều hành tự động cấp phát một Port rảnh (Bind vào port 0)
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.bind(('127.0.0.1', 0))
        self.p2p_port = temp_sock.getsockname()[1] # Lấy số port vừa được cấp
        temp_sock.close() # Đóng socket tạm này lại để lát nữa P2P Listener dùng
        
        try:
            self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_conn.connect((SERVER_HOST, SERVER_PORT))
            self.running = True
            
            # Gửi gói đăng nhập lên Server với Port tự động lấy được
            req = serialize("sign_in", self.username, ip="127.0.0.1", port=self.p2p_port, password=password)
            self.server_conn.sendall(req.encode('utf-8'))
            
            # Mở luồng lắng nghe tin nhắn P2P ngầm
            threading.Thread(target=self.p2p_server_listener, daemon=True).start()
            
            self.start()
        except Exception as e:
            self.login_result.emit(False, f"Lỗi kết nối Server: {e}")
    def run(self):
        buffer = ""
        while self.running:
            try:
                raw = self.server_conn.recv(BUFFER_SIZE).decode('utf-8')
                if not raw: break
                buffer += raw
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg = deserialize(line)
                    if not msg: continue
                    
                    m_type = msg["type"]
                    if m_type == "sign_in_response":
                        if msg["payload"]["status"] == "success":
                            self.login_result.emit(True, "Thành công")
                        else:
                            self.login_result.emit(False, msg["payload"]["reason"])
                            self.running = False
                    
                    elif m_type == "keep_alive":
                        self.server_conn.sendall(serialize("keep_alive_ack", self.username).encode('utf-8'))
                    
                    # Tách riêng luồng xử lý danh sách online
                    elif m_type == "client_status":
                        self.last_online_list = msg["payload"] # Lưu đệm lại
                        self.update_online_list.emit(msg["payload"]) # Bắn tín hiệu
                        
                    elif m_type in ["status_update", "error"]:
                        self.system_msg.emit(msg["payload"])
                        
                    elif m_type == "chat_res":
                        self.chat_ready.emit(msg["payload"], msg["ip"], msg["port"])
            except: break
        if self.server_conn: self.server_conn.close()

    def request_chat(self, target_user):
        if self.server_conn:
            req = serialize("chat_req", self.username, payload=target_user)
            self.server_conn.sendall(req.encode('utf-8'))

    def p2p_server_listener(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.p2p_port))
        s.listen(5)
        while self.running:
            try:
                conn, addr = s.accept()
                threading.Thread(target=self.p2p_client_handler, args=(conn,), daemon=True).start()
            except: break
            
    def p2p_client_handler(self, conn):
        buffer = ""
        while self.running:
            try:
                raw = conn.recv(BUFFER_SIZE).decode('utf-8')
                if not raw: break
                buffer += raw
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg = deserialize(line)
                    if msg and msg["type"] == "chat":
                        self.receive_msg.emit(msg["username"], msg["payload"])
            except: break
        conn.close()

    def send_p2p_msg(self, target, ip, port, message):
        try:
            if target not in self.p2p_conns:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, int(port)))
                self.p2p_conns[target] = s
            msg = serialize("chat", self.username, payload=message)
            self.p2p_conns[target].sendall(msg.encode('utf-8'))
            return True
        except Exception as e:
            self.system_msg.emit(f"Lỗi gửi tin tới {target}: {e}")
            if target in self.p2p_conns: del self.p2p_conns[target]
            return False

    def logout(self):
        self.running = False
        if self.server_conn:
            try:
                self.server_conn.sendall(serialize("sign_out", self.username).encode('utf-8'))
                self.server_conn.close()
            except: pass