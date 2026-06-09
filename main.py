# main.py
import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMessageBox

from login import Ui_port
from chat import Ui_MainWindow
from client_core import NetworkManager
class ChatController(QtWidgets.QMainWindow):
    def __init__(self, network_mgr):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.net = network_mgr
        self.current_target = None
        self.target_ip = None
        self.target_port = None
        
        self.ui.lineEdit.clear()
        
        # 1. KẾT NỐI SỰ KIỆN GIAO DIỆN
        self.ui.send_button.clicked.connect(self.send_message)
        self.ui.lineEdit.returnPressed.connect(self.send_message)
        self.ui.List_online.itemDoubleClicked.connect(self.on_user_selected)
        
        # 2. KẾT NỐI TÍN HIỆU MẠNG
        self.net.system_msg.connect(self.display_system_msg)
        self.net.update_online_list.connect(self.display_online_list) # Nhận tín hiệu mới
        self.net.chat_ready.connect(self.on_chat_ready)
        self.net.receive_msg.connect(self.display_chat_msg)
        
        # FIX RACE CONDITION: Nếu danh sách online đã được tải về trong lúc UI đang nạp, lấy ra dùng luôn
        if self.net.last_online_list:
            self.display_online_list(self.net.last_online_list)
            
        self.ui.Chat_1.append(f"<b>[HỆ THỐNG]</b> Xin chào {self.net.username}! Nhấp đúp vào một người bên trái để bắt đầu chat.")

    def display_online_list(self, payload):
        """Hàm chuyên dụng để render danh sách online"""
        self.ui.List_online.clear()
        if not payload: return
        users = payload.split(",")
        for u in users:
            self.ui.List_online.addItem(u.strip())

    def display_system_msg(self, msg):
        """Hàm này giờ chỉ thuần túy in thông báo văn bản (VD: [+] Hoa vừa online)"""
        self.ui.Chat_1.append(f"<b>[HỆ THỐNG]</b> <i>{msg}</i>")

    def display_chat_msg(self, sender, msg):
        self.ui.Chat_1.append(f"<font color='blue'><b>[{sender}]:</b></font> {msg}")

    def on_user_selected(self, item):
        full_text = item.text()
        target_username = full_text.split(" ")[0]
        
        if target_username == self.net.username:
            QtWidgets.QMessageBox.information(self, "Thông báo", "Bạn không thể tự chat với chính mình!")
            return
            
        self.ui.Chat_1.append(f"<i>Đang xin thông tin kết nối tới {target_username}...</i>")
        self.net.request_chat(target_username)
        
    def on_chat_ready(self, target, ip, port):
        self.current_target = target
        self.target_ip = ip
        self.target_port = port
        self.ui.Chat_1.append(f"<font color='green'><b>[!] Đã kết nối P2P với {target}. Bạn có thể bắt đầu nhắn tin.</b></font>")

    def send_message(self):
        msg = self.ui.lineEdit.text().strip()
        if not msg: return
        
        if not self.current_target:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhấp đúp vào một người trong danh sách Online để chọn người nhận!")
            return
            
        success = self.net.send_p2p_msg(self.current_target, self.target_ip, self.target_port, msg)
        
        if success:
            self.ui.Chat_1.append(f"<font color='red'><b>[Bạn]:</b></font> {msg}")
            self.ui.lineEdit.clear()

    def closeEvent(self, event):
        self.net.logout()
        event.accept()
class LoginController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_port()
        self.ui.setupUi(self)
        
        self.ui.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.ui.Username.clear()
        self.ui.password.clear()
        
        # [THÊM MỚI] Ẩn hoàn toàn ô nhập Port và chữ "Port:" trên giao diện
        self.ui.Port.hide()
        self.ui.label_3.hide() 
        
        self.net = NetworkManager()
        self.net.login_result.connect(self.handle_login_response)
        self.ui.login.clicked.connect(self.on_login_click)

    def on_login_click(self):
        username = self.ui.Username.text().strip()
        password = self.ui.password.text().strip()
        
        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Username và Password!")
            return
            
        self.ui.login.setEnabled(False) 
        # Gọi hàm xử lý mạng (Không cần truyền Port thủ công nữa)
        self.net.connect_and_login(username, password)

    def handle_login_response(self, is_success, reason):
        self.ui.login.setEnabled(True)
        if is_success:
            self.chat_window = ChatController(self.net)
            self.chat_window.show()
            self.close()
        else:
            QtWidgets.QMessageBox.critical(self, "Đăng nhập thất bại", reason)
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LoginController()
    window.show()
    sys.exit(app.exec())