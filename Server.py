import socket
import threading
import os

HOST = "127.0.0.1"
PORT = 65432
SIZE = 1024  # Kích thước bộ đệm

# Tạo file list từ file text
def downloadFile():
    files = {}
    try:
        with open('namefile.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:  # Bỏ qua các dòng trống
                    continue
                # Kiểm tra nếu dòng có đúng định dạng
                parts = line.split()
                if len(parts) != 2:
                    print(f"[ERROR] Dòng không hợp lệ: {line}")
                    continue
                
                name, size_with_unit = parts
                size, unit = size_with_unit[:-2], size_with_unit[-2:]
                
                if unit == "MB":
                    size_in_bytes = int(size) * 1024 * 1024  # Chuyển MB sang bytes
                elif unit == "GB":
                    size_in_bytes = int(size) * 1024 * 1024 * 1024  # Chuyển GB sang bytes
                else:
                    print(f"[ERROR] Đơn vị không hợp lệ: {unit} trong dòng: {line}")
                    continue

                files[name] = size_in_bytes  # Lưu vào từ điển
    except FileNotFoundError:
        print("File file.txt không tồn tại!")
    return files

def sendChunk(conn, file_name, offset, chunk_size):
    """Gửi phần chunk của file cho client."""
    try:
        with open(file_name, 'rb') as f:
            f.seek(offset)
            data = f.read(chunk_size)
            conn.sendall(data)
    except Exception as e:
        print(f"Lỗi khi gửi chunk: {e}")
        conn.sendall(b"ERROR")

def handleClient(conn, addr, files):
    """Xử lý yêu cầu từ client."""
    print(f"[SERVER] Kết nối với {addr}")
    
    # Gửi danh sách file cho client
    file_list = "\n".join(f"{name} {size // (1024 * 1024)}MB" for name, size in files.items())
    conn.sendall(file_list.encode())

    while True:
        # Nhận yêu cầu tải file
        request = conn.recv(SIZE).decode()
        if not request:
            break
        print(f"[SERVER] Nhận yêu cầu tải file: {request}")

        # Phân tách yêu cầu và gửi phần chunk
        file_name, offset, chunk_size = request.split()
        offset, chunk_size = int(offset), int(chunk_size)

        if file_name in files and os.path.exists(file_name):
            sendChunk(conn, file_name, offset, chunk_size)
        else:
            conn.sendall(b"ERROR")
    
    conn.close()
    print(f"[SERVER] Ngắt kết nối với {addr}")

def startServer():
    """Khởi động server."""
    files = downloadFile()  # Tải danh sách file
    if not files:
        print("Không có file nào để tải!")
        return
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[SERVER] Đang lắng nghe tại {HOST}:{PORT}")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handleClient, args=(conn, addr, files)).start()

if __name__ == "__main__":
    startServer()
