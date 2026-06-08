# common.py
import json

def serialize(msg_type, username, ip="", port="", payload="", password=""):
    """Đóng gói dữ liệu thành JSON string, kết thúc bằng ký tự ngắt dòng"""
    msg = {
        "type": msg_type,
        "username": username,
        "ip": str(ip),
        "port": str(port),
        "payload": payload,
        "password": password
    }
    return json.dumps(msg) + "\n"

def deserialize(raw_data):
    """Giải mã chuỗi JSON thành Dictionary"""
    try:
        return json.loads(raw_data.strip())
    except:
        return None