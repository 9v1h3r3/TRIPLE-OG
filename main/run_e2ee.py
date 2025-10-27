# -*- coding: utf-8 -*-
import time
import random
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pickle

class E2EEBot:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.messages_sent = 0
        self.config = self.load_config()
        
    def load_config(self):
        """कॉन्फ़िग लोड करें"""
        default_config = {
            "e2ee_url": "https://www.facebook.com/messages/e2ee/t/",
            "delay": 20,
            "min_delay": 15,
            "max_delay": 40,
            "messages_file": "data/messages.txt",
            "cookies_file": "data/cookies/fb_e2ee_cookies.pkl",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            with open('main/config.json', 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            print("⚠️  कॉन्फ़िग फाइल नहीं मिली, डिफॉल्ट यूज़ कर रहा हूं")
            
        return default_config
    
    def setup_driver(self):
        """ब्राउज़र सेटअप करें - E2EE के लिए खास"""
        print("🖥️  E2EE ब्राउज़र सेटअप हो रहा है...")
        
        options = Options()
        
        # E2EE के लिए जरूरी सेटिंग्स
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-data-dir=./profiles/chrome_profile")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        
        # User agent सेट करें
        options.add_argument(f"--user-agent={self.config['user_agent']}")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"❌ ब्राउज़र सेटअप में error: {e}")
            return False
    
    def login_to_e2ee(self):
        """E2EE चैट में लॉगिन करें"""
        if not self.driver:
            if not self.setup_driver():
                return False
        
        print("🔐 E2EE चैट में लॉगिन कर रहा हूं...")
        
        try:
            # E2EE URL पर जाएं
            self.driver.get(self.config['e2ee_url'])
            time.sleep(5)
            
            # पहले कुकीज लोड करने की कोशिश करें
            if self.load_cookies():
                self.driver.refresh()
                time.sleep(5)
                print("✅ कुकीज से लॉगिन सफल!")
                return True
            
            print("""
            ====================================
            🤖 MANUAL LOGIN REQUIRED
            ====================================
            
            1. अब Facebook का login page खुलेगा
            2. अपना username/password डालें
            3. 2-factor authentication complete करें
            4. E2EE chat में पहुंचने के बाद ENTER दबाएं
            
            ====================================
            """)
            
            input("👉 लॉगिन complete होने के बाद ENTER दबाएं: ")
            
            # कुकीज सेव करें
            self.save_cookies()
            print("✅ लॉगिन सफल! कुकीज सेव हो गईं")
            return True
            
        except Exception as e:
            print(f"❌ लॉगिन में error: {e}")
            return False
    
    def save_cookies(self):
        """कुकीज सेव करें"""
        try:
            os.makedirs("data/cookies", exist_ok=True)
            with open(self.config['cookies_file'], "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            print("💾 कुकीज सेव हो गईं")
        except Exception as e:
            print(f"❌ कुकीज सेव करने में error: {e}")
    
    def load_cookies(self):
        """कुकीज लोड करें"""
        try:
            with open(self.config['cookies_file'], "rb") as f:
                cookies = pickle.load(f)
            
            # सभी कुकीज ऐड करें
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    continue
            
            print("🍪 कुकीज लोड हो गईं")
            return True
        except FileNotFoundError:
            print("⚠️  कोई सेव्ड कुकीज नहीं मिलीं")
            return False
        except Exception as e:
            print(f"❌ कुकीज लोड करने में error: {e}")
            return False
    
    def load_messages(self):
        """मैसेजेस लोड करें"""
        try:
            with open(self.config['messages_file'], 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            
            print(f"📨 {len(messages)} मैसेज लोड हो गए")
            return messages
        except Exception as e:
            print(f"❌ मैसेज लोड करने में error: {e}")
            return []
    
    def find_e2ee_elements(self):
        """E2EE चैट के elements ढूंढें"""
        try:
            # Message box ढूंढें
            message_box = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox'], div[contenteditable='true']"))
            )
            
            # Send button ढूंढें
            send_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Send'][role='button'], button[type='submit']"))
            )
            
            return message_box, send_button
        except Exception as e:
            print(f"❌ E2EE elements नहीं मिले: {e}")
            return None, None
    
    def send_e2ee_message(self, message):
        """E2EE चैट में मैसेज भेजें"""
        try:
            message_box, send_button = self.find_e2ee_elements()
            
            if not message_box or not send_button:
                print("❌ मैसेज बॉक्स या सेंड बटन नहीं मिला")
                return False
            
            # पुराना टेक्स्ट क्लियर करें
            message_box.clear()
            
            # नया मैसेज टाइप करें
            message_box.send_keys(message)
            time.sleep(2)
            
            # मैसेज भेजें
            send_button.click()
            time.sleep(3)
            
            self.messages_sent += 1
            print(f"✅ [{self.messages_sent}] E2EE मैसेज भेज दिया: {message}")
            return True
            
        except Exception as e:
            print(f"❌ मैसेज भेजने में error: {e}")
            return False
    
    def start_auto_messaging(self):
        """ऑटो मैसेजिंग शुरू करें"""
        if not self.driver:
            print("❌ पहले लॉगिन करें (Option 1)")
            return
        
        messages = self.load_messages()
        if not messages:
            print("❌ कोई मैसेज नहीं मिले")
            return
        
        print(f"""
        ====================================
        🤖 E2EE AUTO MESSAGING STARTING...
        ====================================
        
        📝 Total Messages: {len(messages)}
        ⏰ Delay Range: {self.config['min_delay']}-{self.config['max_delay']}s
        🔒 E2EE Chat: ACTIVE
        
        🛑 Stop with: CTRL+C
        ====================================
        """)
        
        input("👉 शुरू करने के लिए ENTER दबाएं...")
        
        self.is_running = True
        message_index = 0
        
        try:
            while self.is_running and messages:
                current_message = messages[message_index]
                
                # मैसेज भेजें
                if self.send_e2ee_message(current_message):
                    message_index = (message_index + 1) % len(messages)
                    
                    # रैंडम डिले
                    delay = random.randint(self.config['min_delay'], self.config['max_delay'])
                    print(f"⏳ अगला मैसेज {delay} सेकंड में...")
                    
                    # डिले with interrupt check
                    for i in range(delay):
                        if not self.is_running:
                            break
                        time.sleep(1)
                else:
                    print("🔄 मैसेज फेल, रिट्रायिंग...")
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            print("\n⏹️  ऑटो मैसेजिंग रोक दी गई")
        except Exception as e:
            print(f"❌ सिस्टम error: {e}")
        finally:
            self.is_running = False
    
    def change_settings(self):
        """सेटिंग्स बदलें"""
        print("\n⚙️  बॉट सेटिंग्स")
        
        try:
            print(f"वर्तमान डिले: {self.config['delay']}s")
            new_delay = input("नया डिले (सेकंड में): ")
            if new_delay:
                self.config['delay'] = int(new_delay)
            
            print(f"मिनिमम डिले: {self.config['min_delay']}s")
            new_min = input("नया मिनिमम डिले: ")
            if new_min:
                self.config['min_delay'] = int(new_min)
            
            print(f"मैक्सिमम डिले: {self.config['max_delay']}s")
            new_max = input("नया मैक्सिमम डिले: ")
            if new_max:
                self.config['max_delay'] = int(new_max)
            
            # कॉन्फ़िग सेव करें
            with open('main/config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            
            print("✅ सेटिंग्स सेव हो गईं")
            
        except ValueError:
            print("❌ गलत वैल्यू! नंबर डालें")
        except Exception as e:
            print(f"❌ सेटिंग्स सेव करने में error: {e}")
    
    def manage_messages(self):
        """मैसेजेस मैनेज करें"""
        print("\n📝 मैसेज मैनेजमेंट")
        print("1. मैसेजेस देखें")
        print("2. नया मैसेज ऐड करें")
        print("3. मैसेज डिलीट करें")
        
        choice = input("👉 चुनाव करें: ")
        
        try:
            if choice == '1':
                messages = self.load_messages()
                for i, msg in enumerate(messages, 1):
                    print(f"{i}. {msg}")
                    
            elif choice == '2':
                new_msg = input("नया मैसेज डालें: ")
                with open(self.config['messages_file'], 'a', encoding='utf-8') as f:
                    f.write(new_msg + '\n')
                print("✅ मैसेज ऐड हो गया")
                
            elif choice == '3':
                messages = self.load_messages()
                for i, msg in enumerate(messages, 1):
                    print(f"{i}. {msg}")
                
                msg_num = int(input("डिलीट करने के लिए मैसेज नंबर डालें: ")) - 1
                if 0 <= msg_num < len(messages):
                    del messages[msg_num]
                    with open(self.config['messages_file'], 'w', encoding='utf-8') as f:
                        for msg in messages:
                            f.write(msg + '\n')
                    print("✅ मैसेज डिलीट हो गया")
                else:
                    print("❌ गलत मैसेज नंबर")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_status(self):
        """स्टेटस दिखाएं"""
        print(f"""
        ====================================
        📊 BOT STATUS
        ====================================
        
        🤖 बॉट स्टेटस: {'RUNNING' if self.is_running else 'STOPPED'}
        📨 मैसेज भेजे: {self.messages_sent}
        🔗 ड्राइवर: {'ACTIVE' if self.driver else 'INACTIVE'}
        ⏰ डिले: {self.config['delay']}s
        
        ====================================
        """)
    
    def cleanup(self):
        """क्लीनअप"""
        self.is_running = False
        if self.driver:
            self.driver.quit()
            print("🧹 ब्राउज़र बंद हो गया")
