# config.py
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9999
BUFFER_SIZE = 2048

# Thời gian Keep-Alive (giây)
HEARTBEAT_INTERVAL = 5   # Server gửi ping mỗi 5s
TIMEOUT_LIMIT = 15       # Nếu sau 15s không nhận được ack -> Remove