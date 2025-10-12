# Messenger Multi-User Panel

🔥 **Multi-User Facebook Messenger Bot Control Panel** 🔥

Ye project ek **web-based control panel** hai jisme multiple users apne Facebook cookies, targets, messages aur prefix set karke messages send kar sakte hain. Bot random delays ke saath message bhejta hai aur real-time logs show karta hai.

---

## Features

- ✅ Multi-user panel (har user apna bot start/stop kare)  
- ✅ Cookie paste option per user  
- ✅ Prefix support for messages  
- ✅ Target IDs as text input  
- ✅ Message upload via `.txt` file  
- ✅ Random delay per message (4–10 sec)  
- ✅ Real-time logs (last 2 messages only)  
- ✅ Start/Stop buttons per user  
- ✅ Tailwind CSS + dark theme  
- ✅ Docker ready + 24/7 uptime compatible  

---

## Folder Structure
---

## Requirements

- Python 3.13+  
- Docker (optional, recommended for 24/7 uptime)  
- Node.js + npm (optional, if building Tailwind locally)  

---

## Installation & Setup

### 1️⃣ Using Docker (Recommended)


```bash
# Build Docker image
docker build -t messenger-panel .

# Run Docker container
docker run -d -p 8080:8080 messenger-panel
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Run Flask app
python app.py
