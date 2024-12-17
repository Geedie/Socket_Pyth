import socket
import os
import threading

HOST = "127.0.0.1"
PORT = 65432
SIZE = 1024  # Kích thước bộ đệm

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
            with open(part_file, "rb") as pf:
                f.write(pf.read())
            os.remove(part_file)  # Xóa file tạm
    print(f"[CLIENT] File {file_name} đã tải xong.")

def updateprogress(file_name, part_num, total_parts):
    """Cập nhật tiến độ tải trên màn hình."""
    progress = (part_num / total_parts) * 100
    print(f"Downloading {file_name} part {part_num + 1} ... {int(progress)}%")

def startClient():
    """Khởi động client."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        print("[CLIENT] Đã kết nối tới server!")

        # Nhận danh sách file từ server
        file_list = client.recv(SIZE).decode()
        print("Danh sách file từ server:")
        print(file_list)

        # Đọc danh sách file cần tải từ input.txt
        with open('input.txt', 'r') as f:
            files_to_download = [line.strip() for line in f.readlines() if line.strip()]

        # Xử lý từng file trong danh sách
        for file_name in files_to_download:
            print(f"Đang tải file {file_name}...")
            try:
                file_size = int(input(f"Nhập kích thước file {file_name} (MB): ")) * 1024 * 1024
                chunk_size = file_size // 4  # Chia file thành 4 phần

                threads = []
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
            except ValueError:
                print(f"[CLIENT] Lỗi khi nhập kích thước cho {file_name}, vui lòng kiểm tra lại!")
                
    except Exception as e:
        print(f"[CLIENT] Lỗi khi kết nối tới server: {e}")

if __name__ == "__main__":
    startClient()
