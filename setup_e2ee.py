# -*- coding: utf-8 -*-
import os

def create_e2ee_files():
    """E2EE बॉट के लिए सभी जरूरी फाइल्स बनाएं"""
    
    files_config = {
        "tid.txt": "100000000000000",  # अपना Facebook Thread ID डालें
        "time.txt": "2",               # डिले टाइम (सेकंड में)
        "cookies.txt": """# Facebook Cookies - यहाँ अपनी कुकीज पेस्ट करें
# Format: domain<TAB>TRUE<TAB>path<TAB>secure<TAB>expiration<TAB>name<TAB>value
.facebook.com	TRUE	/	TRUE	1735689999	xs	PASTE_YOUR_XS_COOKIE_HERE
.facebook.com	TRUE	/	TRUE	1735689999	c_user	PASTE_YOUR_USER_ID_HERE
.facebook.com	TRUE	/	TRUE	1735689999	fr	PASTE_YOUR_FR_COOKIE_HERE
""",
        "prefix.txt": "🤖 [E2EE]: ",
        "messages.txt": """नमस्ते! यह E2EE encrypted message है
कैसे हो? यह secure chat है
E2EE encryption active है
Automated messaging test
अंतिम टेस्ट मैसेज"""
    }
    
    for filename, content in files_config.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filename} बन गई")
        else:
            print(f"⚠️  {filename} पहले से exists")
    
    print("\n🎉 सभी E2EE फाइल्स तैयार हैं!")
    print("👉 अब इन फाइल्स को एडिट करें:")
    print("   - tid.txt: अपना Facebook Thread ID डालें")
    print("   - time.txt: डिले टाइम (सेकंड में)")
    print("   - cookies.txt: अपनी Facebook कुकीज पेस्ट करें")

if __name__ == "__main__":
    create_e2ee_files()
