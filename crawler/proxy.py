import requests
import time
import json

class RotatingProxy:
    def __init__(self, proxy_key):
        self.proxy_key = proxy_key
        self.current_proxy = None
        self.last_proxy_change = 0
        self.min_proxy_time = 60
        
    def get_new_proxy(self):
        try:
            # Tạo URL request đến API proxy xoay
            api_url = f"https://proxyxoay.shop/api/get.php?key={self.proxy_key}&nhamang=random&tinhthanh=0"
            
            # Gọi API để lấy proxy mới
            response = requests.get(api_url, timeout=10)
            
            # Kiểm tra xem response có thành công không
            if response.status_code == 200:
                proxy_data = json.loads(response.text)
                
                # In thông báo ngắn gọn
                if "message" in proxy_data:
                    print(f"API proxy: {proxy_data['message']}")
                
                # Trước tiên thử lấy proxy HTTP
                proxy_str = None
                if "proxyhttp" in proxy_data and proxy_data["proxyhttp"]:
                    proxy_str = proxy_data["proxyhttp"]
                    print("Đã nhận proxy HTTP mới")
                else:
                    print("Không tìm thấy thông tin proxy trong phản hồi API")
                    return None
                
                # Tách thông tin proxy
                proxy_parts = proxy_str.split(":")
                
                # Đảm bảo đủ 4 phần: ip, port, username, password
                if len(proxy_parts) == 4:
                    proxy_info = {
                        "ip": proxy_parts[0],
                        "port": proxy_parts[1],
                        "username": proxy_parts[2],
                        "password": proxy_parts[3]
                    }
                    
                    # Cập nhật current_proxy và thời gian thay đổi
                    self.current_proxy = proxy_info
                    self.last_proxy_change = time.time()
                    
                    # In thông tin proxy đã nhận - chỉ hiển thị IP và port
                    print(f"Proxy mới: {proxy_info['ip']}:{proxy_info['port']}")
                    
                    return proxy_info
                else:
                    print(f"Định dạng proxy không hợp lệ, thử lại sau...")
            else:
                print(f"Lỗi API proxy: {response.status_code}")
                
        except Exception as e:
            print(f"Lỗi khi lấy proxy mới: {str(e)}")
        
        return None