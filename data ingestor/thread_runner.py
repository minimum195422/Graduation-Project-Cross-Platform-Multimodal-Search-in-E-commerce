import threading
from data_management import worker

def run_threads(num_threads=10):
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    print("Khởi chạy hệ thống tiêu thụ đa luồng từ SQS...")
    run_threads()
