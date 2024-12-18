import socket
import os
import threading
import time
import signal

HOST = "127.0.0.1"
PORT = 65432
SIZE = 1024  # Kích thước bộ đệm

# Biến toàn cục để theo dõi trạng thái chương trình
running = True

def signal_handler(sig, frame):
    """Xử lý tín hiệu Ctrl+C để kết thúc chương trình."""
    global running
    running = False
    print("\n[CLIENT] Đang thoát chương trình...")

signal.signal(signal.SIGINT, signal_handler)

def downloadChunk(file_name, part_num, offset, chunk_size):
    """Tải một phần (chunk) của file từ server."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        # Yêu cầu gửi chunk
        request = f"{file_name} {offset} {chunk_size}"
        client.sendall(request.encode())

        # Nhận dữ liệu và ghi vào file tạm
        with open(f"{file_name}.part{part_num}", "wb") as f:
            while chunk_size > 0:
                data = client.recv(min(SIZE, chunk_size))
                if not data:
                    break
                f.write(data)
                chunk_size -= len(data)
        print(f"[CLIENT] Đã tải phần {part_num + 1} của {file_name}")
    except Exception as e:
        print(f"[CLIENT] Lỗi khi tải phần {part_num + 1} của {file_name}: {e}")
    finally:
        client.close()

def joinfile(file_name, parts):
    """Ghép các phần đã tải thành file hoàn chỉnh."""
    with open(file_name, "wb") as f:
        for part_num in range(parts):
            part_file = f"{file_name}.part{part_num}"
            if os.path.exists(part_file):  # Kiểm tra xem file tạm có tồn tại không
                with open(part_file, "rb") as pf:
                    f.write(pf.read())
                os.remove(part_file)  # Xóa file tạm
    print(f"[CLIENT] File {file_name} đã tải xong.")

def check_file_size(file_name, expected_size):
    """Kiểm tra tổng dung lượng file sau khi nối."""
    actual_size = os.path.getsize(file_name)
    if actual_size == expected_size:
        print(f"[CLIENT] Dung lượng file {file_name} hợp lệ: {actual_size} bytes")
    else:
        print(f"[CLIENT] Dung lượng file {file_name} không hợp lệ: {actual_size} bytes (mong đợi {expected_size} bytes)")

def updateprogress(file_name, part_num, total_parts):
    """Cập nhật tiến độ tải trên màn hình."""
    progress = (part_num + 1) / total_parts * 100  # Cập nhật tiến độ
    print(f"Downloading {file_name} part {part_num + 1} .... {int(progress)}%")

def scan_input_file():
    """Quét file input.txt để tìm file mới cần tải."""
    try:
        with open('input.txt', 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("[CLIENT] File input.txt không tồn tại!")
        return []

def startClient():
    """Khởi động client."""
    global running
    print("[CLIENT] Đang kết nối tới server!")
    
    while running:
        # Nhận danh sách file từ server
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST, PORT))
            file_list = client.recv(SIZE).decode()
            print("Danh sách file từ server:")
            print(file_list)

            # Đọc danh sách file cần tải từ input.txt
            files_to_download = scan_input_file()

            for file_name in files_to_download:
                print(f"Đang tải file {file_name}...")
                try:
                    file_size = int(input(f"Nhập kích thước file {file_name} (MB): ")) * 1024 * 1024
                    chunk_size = file_size // 4  # Chia file thành 4 phần
                    threads = []

                    # Tải từng phần của file
                    for part_num in range(4):
                        offset = part_num * chunk_size
                        t = threading.Thread(target=downloadChunk, args=(file_name, part_num, offset, chunk_size))
                        threads.append(t)
                        t.start()

                    # Cập nhật tiến độ tải
                    for part_num, t in enumerate(threads):
                        t.join()
                        updateprogress(file_name, part_num, 4)

                    # Ghép các phần lại thành file hoàn chỉnh
                    joinfile(file_name, 4)

                    # Kiểm tra dung lượng file sau khi nối
                    check_file_size(file_name, file_size)

                except ValueError:
                    print(f"[CLIENT] Lỗi khi nhập kích thước cho {file_name}, vui lòng kiểm tra lại!")
            
            # Quét lại danh sách file cần tải sau 5 giây
            time.sleep(5)

        except Exception as e:
            print(f"[CLIENT] Lỗi khi kết nối tới server: {e}")
        finally:
            client.close()

if __name__ == "__main__":
    startClient()
