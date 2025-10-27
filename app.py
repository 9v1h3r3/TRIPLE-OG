import eventlet
eventlet.monkey_patch()  # Must come before any other imports

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import asyncio, threading, json, random
from collections import deque
from playwright.async_api import async_playwright
import uuid

app = Flask(__name__)
app.secret_key = "SUPERSECRET_KEY"
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

user_tasks = {}
user_logs = {}
user_progress = {}

@app.before_request
def assign_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/start', methods=['POST'])
def start():
    user_id = session["user_id"]
    if user_id in user_tasks:
        return "⚠️ Bot already running!"

    cookie_json = request.form['cookie']
    prefix = request.form['prefix']
    targets = [t.strip() for t in request.form['targets'].splitlines() if t.strip()]
    msg_file = request.files['messages']
    messages = [m.strip() for m in msg_file.read().decode().splitlines() if m.strip()]

    if not messages or not targets:
        return "❌ Please provide targets and message file."

    loop = asyncio.new_event_loop()
    task = loop.create_task(run_bot(user_id, cookie_json, prefix, targets, messages))
    user_tasks[user_id] = task
    user_logs[user_id] = deque(maxlen=100)
    user_progress[user_id] = {"sent": 0, "total": len(messages) * len(targets)}

    threading.Thread(target=loop.run_until_complete, args=(task,), daemon=True).start()
    return "✅ Bot started successfully!"

@app.route('/stop', methods=['POST'])
def stop():
    user_id = session["user_id"]
    if user_id in user_tasks:
        task = user_tasks[user_id]
        task.cancel()
        del user_tasks[user_id]
        emit_log(user_id, "⛔ Bot stopped by user")
        return "Bot stopped"
    return "No bot running"

async def run_bot(user_id, cookie_json, prefix, targets, messages):
    try:
        cookies = json.loads(cookie_json)
    except:
        emit_log(user_id, "❌ Invalid cookie JSON")
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.add_cookies(cookies)
            page = await context.new_page()

            total = len(messages) * len(targets)
            sent = 0

            for tid in targets:
                url = f"https://www.facebook.com/messages/e2ee/t/{tid}"
                await page.goto(url)
                await asyncio.sleep(5)

                for msg in messages:
                    try:
                        text = f"{prefix} {msg}"

                        # Try multiple possible selectors for message box
                        selectors = [
                            'div[aria-label="Message"]',
                            'div[contenteditable="true"]',
                            'div[role="textbox"]',
                            'div[aria-label="Type a message..."]'
                        ]

                        input_box = None
                        for sel in selectors:
                            try:
                                await page.wait_for_selector(sel, timeout=10000)
                                input_box = await page.query_selector(sel)
                                if input_box:
                                    break
                            except:
                                continue

                        if not input_box:
                            emit_log(user_id, f"[!] Input box missing for {tid} — refreshing...")
                            await page.reload()
                            await asyncio.sleep(6)
                            continue

                        # ✅ Paste message instantly
                        await input_box.click()
                        await page.evaluate("""text => {
                            const el = document.activeElement;
                            if (el && el.isContentEditable) {
                                el.innerText = text;
                            }
                        }""", text)

                        # ✅ Safer Enter key (no timeout)
                        await page.evaluate("""
                            const el = document.activeElement;
                            if (el) {
                                const evt = new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', bubbles: true});
                                el.dispatchEvent(evt);
                            }
                        """)

                        sent += 1
                        user_progress[user_id]["sent"] = sent
                        socketio.emit("progress_update", user_progress[user_id], room=user_id)
                        emit_log(user_id, f"💬 Sent to {tid}: {msg[:60]}...")

                        await asyncio.sleep(random.uniform(5, 10))  # ✅ delay between 5–10s

                    except asyncio.CancelledError:
                        emit_log(user_id, "⛔ Bot stopped gracefully")
                        await browser.close()
                        return
                    except Exception as e:
                        emit_log(user_id, f"[x] Error while sending to {tid}: {e}")

            await browser.close()
            emit_log(user_id, "✅ Finished sending all messages")

    except Exception as e:
        emit_log(user_id, f"⚠️ Browser error: {e}")

def emit_log(user_id, msg):
    if user_id not in user_logs:
        user_logs[user_id] = deque(maxlen=100)
    user_logs[user_id].append(msg)
    socketio.emit("log_update", msg, room=user_id)

@socketio.on('connect')
def handle_connect():
    user_id = session["user_id"]
    join_room(user_id)
    for msg in user_logs.get(user_id, []):
        emit("log_update", msg, room=user_id)
    if user_id in user_progress:
        emit("progress_update", user_progress[user_id], room=user_id)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
