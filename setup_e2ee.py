# -*- coding: utf-8 -*-
import os
import subprocess
import sys

def setup_e2ee_system():
    print("🔧 E2EE Messenger Bot System Setup...")
    
    # Create directories
    directories = [
        "main",
        "data/cookies", 
        "data/logs",
        "profiles/chrome_profile"
    ]
    
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Folder created: {dir_path}")
    
    # Create messages file
    if not os.path.exists("data/messages.txt"):
        sample_messages = [
            "Hello! This is E2EE encrypted message.",
            "How are you? This is secure chat.",
            "This bot is made for E2EE chats.", 
            "End-to-end encryption is active.",
            "Final test message."
        ]
        
        with open("data/messages.txt", "w", encoding="utf-8") as f:
            for msg in sample_messages:
                f.write(msg + "\n")
        print("✅ Sample messages created")
    
    # Install requirements
    print("📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager"])
    
    print("""
    ====================================
    🎉 E2EE BOT SETUP COMPLETE!
    ====================================
    
    Next Steps:
    1. Run: python run_e2ee_bot.py
    2. Choose Option 1 for login
    3. Manual login required first time
    4. Then use Option 2 for auto messaging
    
    ====================================
    """)

if __name__ == "__main__":
    setup_e2ee_system()
