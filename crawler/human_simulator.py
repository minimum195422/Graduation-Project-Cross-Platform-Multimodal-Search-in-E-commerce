import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class HumanBehaviorSimulator:
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
    
    def random_scroll(self):
        """Di chuyển trang theo hướng ngẫu nhiên với tốc độ khác nhau"""
        scroll_direction = random.choice([-1, 1])  # -1: lên, 1: xuống
        scroll_amount = random.randint(100, 500)  # Số pixel cuộn
        scroll_speed = random.uniform(0.5, 2.0)  # Tốc độ cuộn
        
        # Cuộn với tốc độ thay đổi để giống người thật
        steps = random.randint(2, 5)
        for i in range(steps):
            step_amount = scroll_amount // steps
            self.driver.execute_script(f"window.scrollBy(0, {scroll_direction * step_amount});")
            time.sleep(scroll_speed / steps)
    
    def mouse_hover_random_elements(self):
        """Di chuyển chuột qua các phần tử ngẫu nhiên trên trang"""
        try:
            # Tìm các phần tử tương tác được
            interactive_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "a, button, input, select, .MtXiu, div[role='button']")
            
            if not interactive_elements:
                return
            
            # Chọn một số phần tử ngẫu nhiên để di chuột qua
            num_hovers = random.randint(1, 2)
            chosen_elements = random.sample(interactive_elements, 
                                          min(num_hovers, len(interactive_elements)))
            
            for element in chosen_elements:
                try:
                    self.actions.move_to_element(element).perform()
                    time.sleep(random.uniform(0.3, 1.0))
                except:
                    pass  # Bỏ qua nếu không thể hover
        except:
            pass  # Suppress all errors silently
    
    def change_viewport(self):
        """Thay đổi kích thước viewport ngẫu nhiên trong một phạm vi hợp lý"""
        width = random.randint(1024, 1366)
        height = random.randint(680, 900)
        self.driver.set_window_size(width, height)
    
    def simulate_reading(self):
        """Giả lập thời gian đọc nội dung trên trang"""
        reading_time = random.uniform(2.0, 4.0)
        time.sleep(reading_time)
    
    def random_inactive_time(self):
        """Giả lập thời gian không hoạt động"""
        inactive_time = random.uniform(1.0, 2.0)
        time.sleep(inactive_time)
    
    def perform_random_action(self):
        """Thực hiện một hành động ngẫu nhiên để giả lập hành vi người dùng"""
        actions = [
            self.random_scroll,
            self.mouse_hover_random_elements,
            self.simulate_reading,
            self.random_inactive_time
        ]
        
        # Không nên thực hiện thay đổi viewport quá thường xuyên
        if random.random() < 0.1:  # Chỉ 10% cơ hội thực hiện
            actions.append(self.change_viewport)
            
        # Chọn và thực hiện một hành động ngẫu nhiên
        try:
            chosen_action = random.choice(actions)
            chosen_action()
        except:
            pass  # Suppress all errors silently