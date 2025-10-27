# -*- coding: utf-8 -*-
import os
import sys
from main.e2ee_bot import E2EEBot

def show_menu():
    print("""
    ====================================
    🚀 FACEBOOK E2EE MESSENGER BOT SYSTEM
    ====================================
    
    1. 🔐 E2EE Chat में लॉगिन करें
    2. 🤖 ऑटो मैसेजिंग शुरू करें  
    3. ⚙️ सेटिंग्स बदलें
    4. 📝 मैसेजेस मैनेज करें
    5. 📊 स्टेटस देखें
    6. 🚪 एक्सिट
    
    ====================================
    """)

def main():
    bot = E2EEBot()
    
    while True:
        show_menu()
        choice = input("👉 अपना चुनाव डालें (1-6): ")
        
        if choice == '1':
            bot.login_to_e2ee()
        elif choice == '2':
            bot.start_auto_messaging()
        elif choice == '3':
            bot.change_settings()
        elif choice == '4':
            bot.manage_messages()
        elif choice == '5':
            bot.show_status()
        elif choice == '6':
            print("👋 बाय! सिस्टम बंद हो रहा है...")
            bot.cleanup()
            break
        else:
            print("❌ गलत चुनाव! फिर से कोशिश करें")

if __name__ == "__main__":
    main()
