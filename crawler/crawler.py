from pathlib import Path
import os
import json
import re
import time
import random
import urllib.parse
import requests
import chromedriver_autoinstaller

from datetime import datetime
from dotenv import load_dotenv

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException


from proxy import RotatingProxy
from human_simulator import HumanBehaviorSimulator
from rabbitmq_connector import RabbitMQConnector
from pipelines import upload_file_to_s3, send_sqs_message_from_json, zip_folder


load_dotenv()

class ProductCrawler:
    def __init__(self, proxy_key, name):
        self.proxy_key = proxy_key
        self.name = name
        self.crawl_timestamp = "%d%m%Y_%H%M%S"
        self.proxy_manager = RotatingProxy(proxy_key)
        self.current_proxy = None
        self.last_proxy_change = 0
        self.total_saved_count = 0
        self.stop_event = None

    def get_proxy_config(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_proxy_change

        def try_get_valid_proxy():
            for attempt in range(3):
                proxy_info = self.proxy_manager.get_new_proxy()
                if proxy_info:
                    return proxy_info
                else:
                    print(f"⚠️ {self.name} - Proxy chưa sẵn sàng, thử lại sau 60 giây...")
                    time.sleep(60)
            print(f"❌ {self.name} - Không thể lấy proxy hợp lệ sau nhiều lần thử.")
            return None

        # ⚠️ Nếu chưa đủ 60 giây thì đợi cho đến khi đủ
        if self.current_proxy and elapsed_time < 60:
            wait_time = int(60 - elapsed_time)
            print(f"⏳ {self.name} - Chưa đủ thời gian đổi proxy. Đang chờ {wait_time}s...")
            time.sleep(wait_time)

        # Đổi proxy (sau khi đã đủ 60s)
        new_proxy = try_get_valid_proxy()
        if new_proxy:
            self.current_proxy = new_proxy
            self.last_proxy_change = time.time()
        else:
            print(f"❌ {self.name} - Không đổi được proxy, giữ nguyên proxy cũ và tiếp tục.")

        proxy = self.current_proxy
        if not proxy:
            raise Exception(f"🛑 {self.name}Không có proxy nào khả dụng để tiếp tục.")

        proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
        return {
            'proxy': {'http': proxy_url, 'https': proxy_url},
            'verify_ssl': False,
            'suppress_connection_errors': True,
            'connection_timeout': 60
        }
    
    def get_random_user_agent(self):
        """Trả về User-Agent ngẫu nhiên từ danh sách"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
        ]
        return random.choice(user_agents)

    def setup_driver(self, proxy=None):
        """Khởi tạo trình duyệt Chrome với options phù hợp và proxy sử dụng selenium-wire"""
        chrome_options = Options()
        # Cấu hình cơ bản
        # chrome_options.add_argument("--headless=new")  # Sử dụng headless mới, ít bị phát hiện hơn
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument(f"--lang=vi-VN")
        
        # Giảm tài nguyên
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1280,720")  # Kích thước nhỏ hơn để tiết kiệm RAM
        chrome_options.add_argument("--disable-audio-output")
        chrome_options.add_argument("--disk-cache-size=33554432")  # Cache 32MB
        chrome_options.add_argument("--js-flags=--expose-gc,--max_old_space_size=100")  # Giới hạn bộ nhớ JS
        
        # Ẩn tất cả log console của Chrome
        chrome_options.add_argument("--log-level=3")  # FATAL
        chrome_options.add_experimental_option('excludeSwitches', ["enable-automation", "enable-logging"])
        
        # Tùy chọn nâng cao để tránh phát hiện bot
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 2,  # 2 = block, 0 = allow, 1 = ask
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            # "profile.managed_default_content_settings.images": 2 
        })
        
        chrome_options.add_argument(f"user-agent={self.get_random_user_agent()}")
        
        # Cấu hình seleniumwire options
        seleniumwire_options = {
            'connection_timeout': 60,  # Giảm thời gian timeout
            'verify_ssl': False,       # Tắt xác minh SSL để tăng tốc
            'suppress_connection_errors': True
        }
        
        # Thêm cấu hình proxy nếu được cung cấp
        if proxy:
            seleniumwire_options.update(proxy)


        # ⚠️ Cập nhật đường dẫn thực tế của bạn ở đây
        

        # chrome_options.binary_location = os.getenv('CHROME_BINARY_PATH')

        chromedriver_autoinstaller.install()

        driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )

        # driver = webdriver.Chrome(
        #     service=Service(os.getenv('CHROMEDRIVER_PATH')),
        #     options=chrome_options,
        #     seleniumwire_options=seleniumwire_options
        # )


        # Tạo driver với selenium-wire
        # driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)
        
        # Thiết lập page load timeout hợp lý
        driver.set_page_load_timeout(30)
        
        # Cài đặt Stealth JavaScript
        stealth_js = """
        // Ẩn WebDriver
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // Ẩn Chrome automation
        window.navigator.chrome = { runtime: {} };
        
        // Giả lập điểm chuột
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        
        // Ẩn plugins và mime types
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/pdf"},
                    description: "Portable Document Format",
                    suffixes: "pdf",
                    type: "application/pdf",
                    name: "PDF Viewer"
                }
            ]
        });
        
        // Giả lập ngôn ngữ thực tế
        Object.defineProperty(navigator, 'languages', {
            get: () => ['vi-VN', 'vi', 'en-US', 'en']
        });
        """
        driver.execute_script(stealth_js)
        
        return driver

    def generate_product_id(self, url):
        from hashlib import md5
        parsed = urllib.parse.urlparse(url)
        norm_url = parsed.netloc + parsed.path.rstrip('/')
        return md5((norm_url + str(len(parsed.path))).encode()).hexdigest()

    def generate_timestamped_folder(self, prefix, base_dir):
        time_str = self.crawl_timestamp
        folder_name = f"{prefix}_{time_str}_{os.getenv('MACHINE')}"
        return os.path.join(base_dir, folder_name)

    def update_storage_folders(self):
        self.image_folder = self.generate_timestamped_folder("image", "image")
        self.json_folder = self.generate_timestamped_folder("json", "json")
        os.makedirs(self.image_folder, exist_ok=True)
        os.makedirs(self.json_folder, exist_ok=True)

    def download_image(self, url, path, proxies, retries=3, delay=2):
        for attempt in range(1, retries + 1):
            try:
                r = requests.get(url, proxies=proxies, timeout=10)
                if r.status_code == 200 and len(r.content) > 100:
                    with open(path, 'wb') as f:
                        f.write(r.content)
                    return True
            except:
                pass
            time.sleep(delay)
        return False

    def clean_price(self, price_str):
        if not price_str:
            return None
        price_digits = re.sub(r'[^0-9]', '', price_str)
        try:
            return int(price_digits)
        except:
            return None

    def parse_rating(self, rating_str):
        try:
            return float(rating_str.split('/')[0].strip())
        except:
            return None
        
    def save_product(self, product):
        pid = self.generate_product_id(product['store_url'])
        product["id"] = pid
        ext = ".jpg"
        image_filename = f"{pid}{ext}"
        image_path = os.path.join(self.image_folder, image_filename)
        json_path = os.path.join(self.json_folder, f"{pid}.json")
        

        s3_image_key = f"images/{os.path.basename(self.image_folder)}/{image_filename}"
        s3_json_key = f"jsons/{os.path.basename(self.json_folder)}/{pid}.json"
        s3_url = f"https://e-commerce-data-lake.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_image_key}"

        image_exists = os.path.exists(image_path)
        json_exists = os.path.exists(json_path)

        if image_exists and json_exists:
            print(f"⚠️ {self.name} - Sản phẩm đã tồn tại đầy đủ: {pid}, bỏ qua")
            return False

        # Lưu lại URL ảnh gốc để tải, vì sẽ thay đổi image_url thành S3 sau khi tải xong
        original_image_url = product["image_url"]

        if not image_exists:
            if not self.download_image(original_image_url, image_path, self.current_proxy_config.get('proxy')):
                print(f"❌ {self.name} - Không tải được ảnh: {original_image_url}")
                return False
            else:
                print(f"🖼 {self.name} - Đã tải ảnh: {image_path}")

        # ✅ Sau khi tải ảnh thành công, cập nhật lại image_url thành S3
        product["image_url"] = s3_url

        if not json_exists:
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(product, f, ensure_ascii=False, indent=2)
                print(f"✅ {self.name} - Đã lưu JSON: {json_path}")
            except Exception as e:
                print(f"❌ {self.name} - Lỗi khi lưu JSON: {e}")
                return False

        # ✅ Upload ảnh và JSON lên S3
        try:
            upload_file_to_s3(image_path, s3_path=f"images/{os.path.basename(self.image_folder)}/", crawler_name=self.name)
            upload_file_to_s3(json_path, s3_path=f"jsons/{os.path.basename(self.json_folder)}/", crawler_name=self.name)
        
            # ✅ Upload JSON lên SQS
            send_sqs_message_from_json(json_path)
        except Exception as e:
            print(f"❌ {self.name} - Không thể upload lên S3: {e}")
            return False

        return True



    def crawl_keyword(self, keyword):
        self.crawl_timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        print(f"[{self.name}] 👉 Crawl keyword: {keyword} → tạo folder timestamp {self.crawl_timestamp}")
        self.update_storage_folders()

        sw_options = self.get_proxy_config()
        self.current_proxy_config = sw_options
        driver = self.setup_driver(sw_options)

        self.last_saved_count = 0  # <-- lưu số lượng sản phẩm thành công cho mỗi keyword

        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&tbm=shop&hl=vi&gl=vn"
            driver.get(url)

            page_source = driver.page_source
            if "recaptcha" in page_source or "captcha-form" in page_source:
                print(f"{self.name} - Phát hiện CAPTCHA. Bỏ qua keyword: {keyword}")
                return False  # Không ack để requeue

            simulator = HumanBehaviorSimulator(driver)
            simulator.perform_random_action()

            handled = False
            total_saved = 0

            selector_handlers = [
                ("div.MtXiu", self.process_cards_mtXiu),
                ("div.LrTUQ", self.process_cards_LrTUQ)
            ]

            for selector, handler in selector_handlers:
                if self.stop_event.is_set():
                    print(f"{self.name}: Nhận tín hiệu dừng, thoát khỏi crawl_keyword.")
                    break

                try:
                    cards = WebDriverWait(driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"{self.name}: Found {len(cards)} products")
                    if cards:
                        print(f"{self.name} start crawling by {selector} card")
                        total_saved = handler(driver, cards, simulator)
                        handled = True
                        break
                except TimeoutException:
                    pass

            try:
                for folder in [self.image_folder, self.json_folder]:
                    zip_path = zip_folder(folder)
                    if zip_path:
                        if 'json' in folder:
                            s3_subpath = f"archives/json/{os.path.basename(zip_path)}"
                        elif 'image' in folder:
                            s3_subpath = f"archives/image/{os.path.basename(zip_path)}"
                        else:
                            s3_subpath = f"archives/{os.path.basename(zip_path)}"
                        upload_file_to_s3(zip_path, s3_path=s3_subpath, crawler_name=self.name)
            except Exception as e:
                print(f"❌ {self.name} - Lỗi khi zip/upload folder sau crawl: {e}")

            self.last_saved_count = total_saved  # <-- cập nhật số lượng sản phẩm
            return handled and total_saved > 0
        
        except:
            return False
        finally:
            driver.quit()

    def process_cards_mtXiu(self, driver, cards, simulator):
        for i, card in enumerate(cards):
            if self.stop_event.is_set():
                print(f"{self.name}: Nhận tín hiệu dừng, thoát giữa danh sách sản phẩm MtXiu.")
                break

            product = {}
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", card)
                ActionChains(driver).move_to_element(card).pause(2).click().perform()
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mLFOe")))
                simulator.simulate_reading()

                product['timestamp'] = self.crawl_timestamp
                product['image_url'] = driver.find_element(By.CSS_SELECTOR, "div.Cl9jQc img.KfAt4d").get_attribute('src')
                product['name'] = driver.find_element(By.CSS_SELECTOR, "h2.u44bxd").text
                product['store_url'] = driver.find_element(By.XPATH, "//div[contains(@class, 'sCXXQd')]/a").get_attribute('href')

                price_element = card.find_element(By.CSS_SELECTOR, "span.lmQWe")
                product['price'] = price_element.text

                rating_raw = card.find_element(By.CSS_SELECTOR, "span.yi40Hd").text.strip()
                product['rating'] = rating_raw

                reviews_text = driver.find_element(By.CSS_SELECTOR, "span.QJUAn").text
                match = re.search(r'(\d+\.?\d*[KM]?)', reviews_text)
                product['reviews_count'] = match.group(1) if match else "0"

                if self.save_product(product):
                    self.total_saved_count += 1  # ✅ cập nhật biến toàn cục

            except:
                pass

    def process_cards_LrTUQ(self, driver, cards, simulator):
        for i, card in enumerate(cards):
            if self.stop_event.is_set():
                print(f"{self.name}: Nhận tín hiệu dừng, thoát giữa danh sách sản phẩm LrTUQ.")
                break
            product = {}
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", card)
                ActionChains(driver).move_to_element(card).pause(0.5).click().perform()
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mLFOe")))
                simulator.simulate_reading()

                product['timestamp'] = self.crawl_timestamp
                product['image_url'] = driver.find_element(By.CSS_SELECTOR, "div.Cl9jQc img.KfAt4d").get_attribute('src')
                product['name'] = driver.find_element(By.CSS_SELECTOR, "div.bi9tFe").text
                product['store_url'] = driver.find_element(By.XPATH, "//div[contains(@class, 'sCXXQd')]/a").get_attribute('href')

                price_element = card.find_element(By.CSS_SELECTOR, "span.lmQWe")
                product['price'] = price_element.text

                rating_raw = card.find_element(By.CSS_SELECTOR, "span.yi40Hd").text.strip()
                product['rating'] = rating_raw

                reviews_text = driver.find_element(By.CSS_SELECTOR, "span.Bk5Fre").text
                match = re.search(r'(\d+\.?\d*[KM]?)', reviews_text)
                product['reviews_count'] = match.group(1) if match else "0"

                if self.save_product(product):
                    self.total_saved_count += 1  # ✅ cập nhật biến toàn cục

                if i % 5 == 0:
                    simulator.perform_random_action()
            except:
                pass

    def process_cards_new_style(self, driver, cards, simulator):
        pass

    def run(self, stop_event):
        self.stop_event = stop_event

        try:
            def callback(keyword):
                if self.stop_event.is_set():
                    print(f"{self.name} dừng tiêu thụ keyword vì có yêu cầu thoát.")
                    return False
                return self.crawl_keyword(keyword)

            connector = RabbitMQConnector()
            self.connector = connector
            connector.start_safe_consume("keywords", callback)
        except Exception as e:
            print(f"❌ {self.name} gặp lỗi trong run(): {e}")