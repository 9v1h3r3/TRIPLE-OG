# -*- coding: utf-8 -*-
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def find_e2ee_threads():
    """सभी E2EE थ्रेड्स के ID ढूंढें"""
    print("🔍 E2EE थ्रेड्स ढूंढ रहा हूं...")
    
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    
    try:
        # कुकीज लोड करें
        driver.get("https://facebook.com")
        time.sleep(2)
        
        # cookies.txt से कुकीज लोड करें
        with open("cookies.txt", "r") as f:
            for line in f:
                if not line.startswith('#') and line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 7:
                        cookie = {
                            'domain': parts[0],
                            'name': parts[5],
                            'value': parts[6]
                        }
                        try:
                            driver.add_cookie(cookie)
                        except:
                            pass
        
        # मैसेजेस पेज पर जाएं
        driver.get("https://www.facebook.com/messages")
        time.sleep(5)
        
        # E2EE थ्रेड्स ढूंढें
        page_source = driver.page_source
        
        # E2EE थ्रेड पैटर्न
        e2ee_patterns = [
            r'messages/e2ee/t/(\d+)',
            r'thread_id=(\d+)',
            r't/(\d+)\?.*e2ee'
        ]
        
        thread_ids = set()
        
        for pattern in e2ee_patterns:
            found_ids = re.findall(pattern, page_source)
            thread_ids.update(found_ids)
        
        print(f"\n✅ मिले E2EE थ्रेड IDs:")
        for tid in thread_ids:
            print(f"👉 {tid}")
            
        if thread_ids:
            # पहला थ्रेड ID सेव करें
            first_tid = list(thread_ids)[0]
            with open("tid.txt", "w") as f:
                f.write(first_tid)
            print(f"\n💾 पहला Thread ID सेव हो गया: {first_tid}")
        else:
            print("❌ कोई E2EE थ्रेड नहीं मिला")
            
    except Exception as e:
        print(f"❌ एरर: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    find_e2ee_threads()
