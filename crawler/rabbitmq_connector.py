import os
import ssl
import pika
import time
import certifi
from dotenv import load_dotenv
from threading import Lock

class RabbitMQConnector:
    _instance = None
    _lock = Lock()

    def __init__(self):
        load_dotenv()
        host = os.getenv("RABBITMQ_HOST")
        vhost = os.getenv("RABBITMQ_VHOST")
        user = os.getenv("RABBITMQ_USER")
        password = os.getenv("RABBITMQ_PASSWORD")

        amqp_url = f"amqps://{user}:{password}@{host}/{vhost}"
        self.params = pika.URLParameters(amqp_url)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.params.ssl_options = pika.SSLOptions(ssl_context)

        self.connection = None
        self.channel = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def connect(self):
        if self.connection is None or self.connection.is_closed:
            self.connection = pika.BlockingConnection(self.params)
            self.channel = self.connection.channel()

    def declare_queue(self, queue: str):
        """
        Đảm bảo khai báo queue với cùng cấu hình như đã có sẵn trên hệ thống RabbitMQ.
        """
        self.channel.queue_declare(
            queue=queue,
            durable=True,
            exclusive=False,
            auto_delete=False
        )

    def send_message(self, queue: str, message: str):
        self.connect()
        self.declare_queue(queue)
        self.channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
        )
        print(f"📤 Đã gửi message tới queue '{queue}': {message}")

    def start_safe_consume(self, queue: str, process_callback):
        self.connect()
        self.declare_queue(queue)
        self.channel.basic_qos(prefetch_count=1)

        def on_message(ch, method, properties, body):
            try:
                message = body.decode('utf-8')
                print(f"📥 Nhận message từ queue '{queue}': {message}")
                process_callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print("✅ Đã xử lý và ACK")
            except Exception as e:
                print(f"❌ Lỗi xử lý: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_consume(queue=queue, on_message_callback=on_message)

        try:
            print(f"🚀 Bắt đầu tiêu thụ message từ queue '{queue}'...")
            self.channel.start_consuming()
        except Exception as e:
            print(f"❗ Tiêu thụ message dừng lại: {e}")

    def stop_consuming(self):
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
            print("⏹️ Đã dừng tiêu thụ message từ RabbitMQ")


    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("🔌 Đã đóng kết nối RabbitMQ")


if __name__ == "__main__":
    connector = RabbitMQConnector.get_instance()

    product_keywords = [
        # 🛍️ Thời trang & Phụ kiện
        "Áo sơ mi nam Uniqlo Oxford",
        "Váy maxi Zara hoa nhí",
        "Quần jeans nữ Levi’s 501",
        "Áo khoác bomber nam Adidas Originals",
        "Giày sneaker Nike Air Force 1",
        "Túi xách COACH Tabby Shoulder Bag",
        "Kính mát Ray-Ban Jackie Ohh II",
        "Đồng hồ Casio G-Shock GA-2100",
        "Thắt lưng da nam Lacoste",
        "Mũ lưỡi trai MLB New York Yankees",

        # 🏠 Đồ gia dụng & Nội thất
        "Máy hút bụi Dyson V12 Detect Slim",
        "Máy lọc không khí Xiaomi Air Purifier 4 Pro",
        "Nồi chiên không dầu Philips HD9650",
        "Máy pha cà phê Delonghi Dedica EC685",
        "Bộ chăn ga gối Everon Modal 100%",
        "Ghế công thái học Sihoo M57",
        "Đèn ngủ thông minh Xiaomi Mi Bedside Lamp 2",
        "Máy rửa bát Bosch Serie 4 SMS46MI05E",
        "Quạt điều hòa Kangaroo KG50F58",
        "Bếp từ đôi Sunhouse SHB9102",

        # 💻 Công nghệ & Thiết bị điện tử
        "Laptop Apple MacBook Air M2 13 inch",
        "Điện thoại Samsung Galaxy S23 Ultra",
        "Tai nghe không dây Sony WF-1000XM5",
        "Máy tính bảng iPad Pro 11 inch M2",
        "Màn hình LG UltraFine 27UN850-W 4K",
        "Bàn phím cơ Keychron K2 V2",
        "Chuột Logitech MX Master 3S",
        "Ổ cứng di động Seagate Backup Plus 2TB",
        "Máy ảnh Sony Alpha A7 III",
        "Loa Bluetooth JBL Charge 5",

        # 🧴 Làm đẹp & Chăm sóc cá nhân
        "Kem chống nắng La Roche-Posay Anthelios SPF 50",
        "Nước hoa Chanel Coco Mademoiselle EDP",
        "Máy rửa mặt Foreo Luna 3",
        "Son môi MAC Matte Lipstick màu Ruby Woo",
        "Kem dưỡng ẩm CeraVe Moisturizing Cream",
        "Máy duỗi tóc Dyson Corrale",
        "Tinh chất dưỡng da The Ordinary Niacinamide 10% + Zinc 1%",
        "Nước tẩy trang Bioderma Sensibio H2O",
        "Máy sấy tóc Panasonic EH-NA98",
        "Bộ cọ trang điểm Real Techniques Everyday Essentials",

        # 🧸 Mẹ & Bé
        "Xe đẩy em bé Aprica Luxuna Light",
        "Ghế ăn dặm Joie Multiply 6in1",
        "Máy hâm sữa Fatzbaby FB3003SL",
        "Bình sữa Comotomo 250ml",
        "Tã dán Merries size M",
        "Kem chống hăm Bepanthen 100g",
        "Máy hút sữa Medela Pump In Style Advanced",
        "Nôi điện Autoru Eco 2025",
        "Bộ đồ chơi Lego Duplo My First Number Train",
        "Yếm ăn silicon chống thấm nước BabyBjörn",

        # 🏋️‍♂️ Thể thao & Dã ngoại
        "Giày chạy bộ Nike ZoomX Vaporfly Next%",
        "Balo leo núi The North Face Borealis",
        "Đồng hồ thể thao Garmin Forerunner 255",
        "Thảm yoga Liforme Original Mat",
        "Bình nước giữ nhiệt Thermos 1L",
        "Lều cắm trại Naturehike Cloud-Up 2",
        "Gậy trekking Black Diamond Trail Back",
        "Kính bơi Speedo Vanquisher 2.0",
        "Vợt cầu lông Yonex Astrox 99",
        "Bộ tạ tay Bowflex SelectTech 552",

        # 🍳 Nhà bếp & Dụng cụ nấu ăn
        "Nồi cơm điện cao tần Zojirushi NP-HCC10XH",
        "Máy xay sinh tố Vitamix E310",
        "Bộ nồi inox 5 món Fissler Original-Profi Collection",
        "Chảo chống dính Tefal Titanium Excellence 28cm",
        "Lò nướng điện Sharp EO-A384RCSV-BK",
        "Máy ép chậm Hurom H-AA-BBE17",
        "Bộ dao nhà bếp Zwilling Twin Pollux 7 món",
        "Máy làm sữa hạt Ranbem 769S",
        "Máy làm bánh mì Panasonic SD-P104",
        "Máy pha cà phê Espresso Breville BES870XL",

        # 📚 Sách & Văn phòng phẩm
        "Sách 'Đắc nhân tâm' - Dale Carnegie",
        "Sách 'Nhà giả kim' - Paulo Coelho",
        "Bút máy Lamy Safari Fountain Pen",
        "Sổ tay Moleskine Classic Notebook A5",
        "Balo laptop chống sốc Samsonite Tectonic Lifestyle",
        "Ghế văn phòng công thái học Herman Miller Aeron",
        "Đèn bàn học LED Xiaomi Mi LED Desk Lamp 1S",
        "Máy in đa chức năng Canon PIXMA G3010",
        "Bút bi Parker Jotter Stainless Steel",
        "Máy hủy tài liệu Silicon PS-800C",

        # 🐶 Thú cưng
        "Thức ăn cho chó Royal Canin Maxi Adult 15kg",
        "Thức ăn cho mèo Whiskas Adult 1.2kg",
        "Lồng vận chuyển chó mèo IRIS 500",
        "Bàn cào móng cho mèo Catit Style",
        "Dây dắt chó tự động Flexi Classic M 5m",
        "Bát ăn chống trượt Inox Petkit Fresh",
        "Máy lọc nước cho thú cưng Xiaomi Petkit Eversweet 2",
        "Đồ chơi cho chó Kong Classic Medium",
        "Sữa tắm cho chó Bio-Groom Protein Lanolin",
        "Bộ cắt móng cho thú cưng Trixie Deluxe",

        # 🎮 Giải trí & Thiết bị chơi game
        "Máy chơi game Sony PlayStation 5",
        "Máy chơi game Nintendo Switch OLED",
        "Tay cầm Xbox Wireless Controller",
        "Tai nghe chơi game Razer BlackShark V2",
        "Bàn phím cơ chơi game SteelSeries Apex Pro",
        "Chuột chơi game Logitech G502 HERO",
        "Màn hình chơi game ASUS ROG Swift PG259QN 360Hz",
        "Ghế chơi game Secretlab TITAN Evo 2022",
        "Webcam Logitech C920 HD Pro",
        "Micro thu âm Blue Yeti USB Microphone"
    ]

    for name in product_keywords:
        connector.send_message("keywords", name)
        time.sleep(0.1)

    connector.close()
    
    

# if __name__ == "__main__":
#     connector = RabbitMQConnector.get_instance()

#     # Gửi 2 từ khoá, 1 bình thường, 1 có chữ 'lỗi' để test lỗi xử lý
#     connector.send_message("keywords", "áo thun nam")
#     connector.send_message("keywords", "áo thun lỗi")



#     # test_consume_success.py
# import time
# from rabbitmq_connector import RabbitMQConnector

# def process_success(message):
#     print(f"🔧 Đang xử lý (thành công): {message}")
#     time.sleep(5)
#     print(f"✅ Hoàn tất xử lý thành công: {message}")

# if __name__ == "__main__":
#     connector = RabbitMQConnector.get_instance()
#     connector.start_safe_consume("keywords", process_success)



# # test_consume_fail.py
# import time
# from rabbitmq_connector import RabbitMQConnector

# def process_with_error(message):
#     print(f"🔧 Đang xử lý (có thể lỗi): {message}")
#     time.sleep(5)
#     if "lỗi" in message:
#         raise ValueError("Giả lập lỗi xử lý")
#     print(f"✅ Xử lý xong bình thường: {message}")

# if __name__ == "__main__":
#     connector = RabbitMQConnector.get_instance()
#     connector.start_safe_consume("keywords", process_with_error)
