import threading
import time
import datetime
import os
import random
from crawler import ProductCrawler
from collections import defaultdict

LOG_FILE_PATH = "crawler_stats_log.txt"

crawler_stats = defaultdict(int)
stats_lock = threading.Lock()
stop_event = threading.Event()
all_crawlers = {}

def run_crawler(proxy_key, name):
    delay = random.uniform(1, 60)
    print(f"{name} sẽ khởi động sau {delay:.1f} giây...")
    time.sleep(delay)
    try:
        crawler = ProductCrawler(proxy_key, name)
        all_crawlers[proxy_key] = crawler
        crawler.run(stop_event)
    except Exception as e:
        print(f"❌ Lỗi ở crawler {name}: {e}")


def display_stats():
    base_log_dir = "log"
    os.makedirs(base_log_dir, exist_ok=True)

    def get_log_file_path():
        time_str = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
        machine = os.getenv("MACHINE", "UNKNOWN")
        return os.path.join(base_log_dir, f"log_{time_str}_{machine}.txt")

    current_log_file = get_log_file_path()

    while not stop_event.is_set():
        now = datetime.datetime.now()

        timestamp = now.strftime("%H:%M:%S")
        print(f"\n===== CẬP NHẬT SỐ LƯỢNG SẢN PHẨM ({timestamp}) =====")

        total = 0
        log_lines = []

        for proxy_key, crawler in all_crawlers.items():
            count = crawler.total_saved_count
            print(f"{crawler.name} ({proxy_key}): {count} sản phẩm")
            total += count
            log_lines.append(f"{crawler.name} | {count} | {timestamp}")
        log_lines.append(f"Total | {total} | {timestamp}")
        print(f"👉 Tổng cộng: {total} sản phẩm")
        print("============================================================\n")

        with open(current_log_file, 'a', encoding='utf-8') as f:
            for line in log_lines:
                f.write(line + "\n")

        time.sleep(60 - now.second)

def monitor_user_input():
    while not stop_event.is_set():
        user_input = input("Nhập 'q' để dừng crawler: ").strip().lower()
        if user_input == 'q':
            print("Đang dừng toàn bộ hệ thống...")
            stop_event.set()
            break

def main():
    threads = []

    # Đọc danh sách proxy key
    with open("proxy_list.txt", "r") as f:
        proxy_keys = [line.strip() for line in f if line.strip()]

    for idx, key in enumerate(proxy_keys, start=1):
        name = f"Crawler-{idx}"

        t = threading.Thread(target=run_crawler, args=(key, name), daemon=True)
        t.start()
        threads.append(t)

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()

    for crawler in all_crawlers.values():
        if hasattr(crawler, 'connector'):
            crawler.connector.stop_consuming()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()


