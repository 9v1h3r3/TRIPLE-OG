# -*- coding: utf-8 -*-
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os

class E2EEMessenger:
    def __init__(self):
        self.driver = None
        self.config = self.load_config()
    
    def load_config(self):
        """सभी फाइल्स से कॉन्फ़िग लोड करें"""
        config = {
            "thread_id": self.read_file("tid.txt", "100000000000000"),
            "delay_time": self.read_file("time.txt", "2"),
            "cookie_file": "cookies.txt",
            "prefix_file": "prefix.txt",
            "messages_file": "messages.txt"
        }
        return config
    
    def read_file(self, filename, default=""):
        """फाइल से डेटा पढ़ें"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            return default
    
    def setup_browser_e2ee(self):
        """E2EE के लिए ब्राउज़र सेटअप"""
        print("🔒 E2EE ब्राउज़र सेटअप...")
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--user-data-dir=./chrome_data")
        self.driver = webdriver.Chrome(options=options)
    
    def load_cookies_e2ee(self):
        """cookies.txt से E2EE के लिए कुकीज लोड करें"""
        try:
            print("🍪 E2EE कुकीज लोड हो रही हैं...")
            self.driver.get("https://facebook.com")
            time.sleep(2)
            
            cookies_loaded = False
            with open(self.config['cookie_file'], 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 7:
                            cookie = {
                                'domain': parts[0],
                                'name': parts[5],
                                'value': parts[6],
                                'path': parts[2],
                                'secure': parts[3].lower() == 'true'
                            }
                            try:
                                self.driver.add_cookie(cookie)
                                cookies_loaded = True
                            except:
                                continue
            
            if cookies_loaded:
                print("✅ E2EE कुकीज लोड हो गईं")
                return True
            else:
                print("❌ कोई कुकीज नहीं मिलीं")
                return False
                
        except Exception as e:
            print(f"❌ कुकीज एरर: {e}")
            return False
    
    def load_prefix(self):
        """prefix.txt से प्रीफिक्स लोड करें"""
        return self.read_file("prefix.txt", "🤖 ")
    
    def load_messages(self):
        """messages.txt से मैसेज लोड करें"""
        try:
            with open(self.config['messages_file'], 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            return messages if messages else ["Hello from E2EE Bot!"]
        except:
            return ["Hello from E2EE Bot!"]
    
    def get_delay_time(self):
        """time.txt से डिले टाइम पढ़ें"""
        try:
            delay = float(self.config['delay_time'])
            return max(1, delay)  # कम से कम 1 सेकंड
        except:
            return 2  # डिफॉल्ट 2 सेकंड
    
    def send_e2ee_message(self, message):
        """E2EE चैट में मैसेज भेजें"""
        try:
            # E2EE थ्रेड URL
            thread_url = f"https://www.facebook.com/messages/e2ee/t/{self.config['thread_id']}"
            self.driver.get(thread_url)
            time.sleep(3)
            
            # E2EE मैसेज बॉक्स ढूंढें
            message_box = self.driver.find_element(By.CSS_SELECTOR, "div[role='textbox'], div[contenteditable='true']")
            message_box.clear()
            message_box.send_keys(message)
            
            # E2EE सेंड बटन
            send_btn = self.driver.find_element(By.CSS_SELECTOR, "div[aria-label='Send'][role='button']")
            send_btn.click()
            
            print(f"🔒 E2EE मैसेज भेजा: {message}")
            return True
            
        except Exception as e:
            print(f"❌ E2EE मैसेज एरर: {e}")
            return False
    
    def start_e2ee_messaging(self):
        """E2EE ऑटो मैसेजिंग शुरू करें"""
        print("🚀 E2EE मैसेजिंग शुरू हो रही है...")
        
        # ब्राउज़र सेटअप
        self.setup_browser_e2ee()
        
        # कुकीज लोड करें
        if not self.load_cookies_e2ee():
            print("❌ कुकीज लोड नहीं हो पाईं, मैन्युअल लॉगिन चाहिए")
            input("👉 मैन्युअल लॉगिन करें और ENTER दबाएं...")
        
        # डेटा लोड करें
        prefix = self.load_prefix()
        messages = self.load_messages()
        delay_time = self.get_delay_time()
        
        print(f"""
🔍 कॉन्फ़िग सारांश:
📱 Thread ID: {self.config['thread_id']}
⏰ Delay Time: {delay_time} सेकंड
📨 Messages: {len(messages)}
🔤 Prefix: {prefix}
🔒 Mode: E2EE Encrypted
        """)
        
        input("👉 शुरू करने के लिए ENTER दबाएं...")
        
        message_count = 0
        
        try:
            while True:  # अनंत लूप - CTRL+C से रोकें
                for msg in messages:
                    # प्रीफिक्स जोड़ें
                    full_message = f"{prefix}{msg}".strip()
                    
                    # E2EE मैसेज भेजें
                    if self.send_e2ee_message(full_message):
                        message_count += 1
                        
                        # डिले
                        print(f"⏳ अगला मैसेज {delay_time} सेकंड में...")
                        time.sleep(delay_time)
        
        except KeyboardInterrupt:
            print(f"\n🛑 रोका गया! कुल {message_count} E2EE मैसेज भेजे गए")
        
        finally:
            if self.driver:
                self.driver.quit()

# मेन प्रोग्राम
if __name__ == "__main__":
    print("=" * 60)
    print("🔒 FACEBOOK E2EE AUTO MESSENGER")
    print("📁 External Files: tid.txt, time.txt, cookies.txt")
    print("=" * 60)
    
    # फाइल्स चेक करें
    required_files = ["tid.txt", "time.txt", "cookies.txt"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ ये फाइल्स नहीं मिलीं: {', '.join(missing_files)}")
        print("📝 setup_e2ee.py चलाकर फाइल्स बनाएं")
    else:
        # बॉट शुरू करें
        bot = E2EEMessenger()
        bot.start_e2ee_messaging()
