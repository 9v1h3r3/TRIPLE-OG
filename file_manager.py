# -*- coding: utf-8 -*-
import os

class FileManager:
    @staticmethod
    def update_thread_id(new_tid):
        """Thread ID अपडेट करें"""
        with open("tid.txt", "w") as f:
            f.write(str(new_tid))
        print(f"✅ Thread ID अपडेट हो गया: {new_tid}")
    
    @staticmethod
    def update_delay_time(new_delay):
        """डिले टाइम अपडेट करें"""
        with open("time.txt", "w") as f:
            f.write(str(new_delay))
        print(f"✅ Delay Time अपडेट हो गया: {new_delay} सेकंड")
    
    @staticmethod
    def add_message(new_message):
        """नया मैसेज ऐड करें"""
        with open("messages.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{new_message}")
        print(f"✅ मैसेज ऐड हो गया: {new_message}")
    
    @staticmethod
    def show_config():
        """कॉन्फ़िग दिखाएं"""
        files = {
            "Thread ID": "tid.txt",
            "Delay Time": "time.txt", 
            "Prefix": "prefix.txt",
            "Messages": "messages.txt",
            "Cookies": "cookies.txt"
        }
        
        print("\n📊 CURRENT CONFIGURATION:")
        print("=" * 40)
        
        for name, filename in files.items():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if name == "Messages":
                        lines = content.split('\n')
                        print(f"{name}: {len(lines)} messages")
                    else:
                        print(f"{name}: {content[:50]}{'...' if len(content) > 50 else ''}")
            except:
                print(f"{name}: ❌ FILE NOT FOUND")

# उपयोग के उदाहरण
if __name__ == "__main__":
    fm = FileManager()
    fm.show_config()
