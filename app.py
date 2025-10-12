from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import asyncio, threading, json, random
from collections import deque
from playwright.async_api import async_playwright
import uuid

app = Flask(__name__)
app.secret_key = "SUPERSECRET_KEY"
socketio = SocketIO(app, async_mode="threading")

user_tasks = {}
user_logs = {}

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
        return "Bot already running!"

    cookie_json = request.form['cookie']
    prefix = request.form['prefix']
    targets = request.form['targets'].splitlines()
    msg_file = request.files['messages']
    messages = msg_file.read().decode().splitlines()

    loop = asyncio.new_event_loop()
    task = loop.create_task(run_bot(user_id, cookie_json, prefix, targets, messages))
    user_tasks[user_id] = task
    user_logs[user_id] = deque(maxlen=2)

    threading.Thread(target=loop.run_until_complete, args=(task,), daemon=True).start()
    return "Bot started"

@app.route('/stop', methods=['POST'])
def stop():
    user_id = session["user_id"]
    if user_id in user_tasks:
        task = user_tasks[user_id]
        task.cancel()
        del user_tasks[user_id]
        return "Bot stopped"
    return "No bot running"

async def run_bot(user_id, cookie_json, prefix, targets, messages):
    try:
        cookies = json.loads(cookie_json)
    except:
        emit_log(user_id, "❌ Invalid cookie JSON")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(cookies)
        page = await context.new_page()

        for tid in targets:
            url = f"https://www.facebook.com/messages/e2ee/t/{tid.strip()}"
            await page.goto(url)
            await asyncio.sleep(5)

            for msg in messages:
                try:
                    text = f"{prefix} {msg}"
                    input_box = await page.query_selector('div[role="textbox"]')
                    if not input_box:
                        emit_log(user_id, f"[!] Input box missing for {tid}")
                        continue
                    await input_box.click()
                    await input_box.type(text)
                    await input_box.press("Enter")
                    emit_log(user_id, f"💬 Sent to {tid}: {msg[:30]}...")
                    await asyncio.sleep(random.uniform(4,10))
                except asyncio.CancelledError:
                    emit_log(user_id, "⛔ Bot stopped by user")
                    await browser.close()
                    return
                except Exception as e:
                    emit_log(user_id, f"[x] Error: {e}")

        await browser.close()
        emit_log(user_id, "✅ Finished sending messages")

def emit_log(user_id, msg):
    if user_id not in user_logs:
        user_logs[user_id] = deque(maxlen=2)
    user_logs[user_id].append(msg)
    socketio.emit("log_update", msg, room=user_id)

@socketio.on('connect')
def handle_connect():
    user_id = session["user_id"]
    join_room(user_id)
    for msg in user_logs.get(user_id, []):
        emit("log_update", msg, room=user_id)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
