# ✅ Eventlet must be patched FIRST
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import asyncio, threading, json, random, uuid
from collections import deque
from playwright.async_api import async_playwright

# --- Flask & SocketIO setup ---
app = Flask(__name__)
app.secret_key = "SUPERSECRET_KEY"
socketio = SocketIO(app, async_mode="eventlet")

# --- Global storages ---
user_tasks = {}
user_logs = {}


# Assign unique session id
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

    try:
        cookie_json = request.form['cookie']
        prefix = request.form['prefix']
        targets = [t.strip() for t in request.form['targets'].splitlines() if t.strip()]
        msg_file = request.files['messages']
        messages = [m.strip() for m in msg_file.read().decode().splitlines() if m.strip()]
    except Exception as e:
        return f"❌ Invalid form data: {e}"

    # Create new async event loop per user
    loop = asyncio.new_event_loop()
    task = loop.create_task(run_bot(user_id, cookie_json, prefix, targets, messages))
    user_tasks[user_id] = task
    user_logs[user_id] = deque(maxlen=100)

    def start_loop(loop, task):
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()

    threading.Thread(target=start_loop, args=(loop, task), daemon=True).start()
    return "✅ Bot started successfully."


@app.route('/stop', methods=['POST'])
def stop():
    user_id = session["user_id"]
    if user_id in user_tasks:
        task = user_tasks.pop(user_id)
        emit_log(user_id, "🛑 Stop signal received. Closing bot...")
        def cancel_task():
            task.cancel()
        threading.Thread(target=cancel_task).start()
        return "Bot stopped."
    return "No active bot to stop."


# ---------------- Main bot logic ----------------
async def run_bot(user_id, cookie_json, prefix, targets, messages):
    try:
        cookies = json.loads(cookie_json)
    except Exception:
        emit_log(user_id, "❌ Invalid cookie JSON format")
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.add_cookies(cookies)
            page = await context.new_page()

            # Verify login
            await page.goto("https://www.facebook.com/")
            if "login" in page.url.lower():
                emit_log(user_id, "❌ Cookie expired or invalid login session.")
                await browser.close()
                return
            emit_log(user_id, "✅ Logged in successfully.")

            # Non-stop loop for all targets
            while True:
                for tid in targets:
                    url = f"https://www.facebook.com/messages/e2ee/t/{tid}"
                    try:
                        await page.goto(url)
                        await asyncio.sleep(random.uniform(3, 6))

                        input_box = await page.query_selector('div[role="textbox"]')
                        if not input_box:
                            emit_log(user_id, f"⚠️ No message box found for {tid}")
                            continue

                        for msg in messages:
                            text = f"{prefix} {msg}"
                            await input_box.click()
                            await input_box.type(text)
                            await input_box.press("Enter")
                            emit_log(user_id, f"💬 Sent to {tid}: {msg[:50]}...")
                            await asyncio.sleep(random.uniform(4, 9))

                    except asyncio.CancelledError:
                        emit_log(user_id, "⛔ Bot manually stopped.")
                        await browser.close()
                        return
                    except Exception as e:
                        emit_log(user_id, f"[x] Error in {tid}: {e}")
                        await asyncio.sleep(5)

                # 🔁 Repeat forever
                emit_log(user_id, "🔄 Restarting message cycle...")
                await asyncio.sleep(random.uniform(20, 40))

    except Exception as e:
        emit_log(user_id, f"❌ Critical Error: {e}")


# ---------------- Helper logging ----------------
def emit_log(user_id, msg):
    if user_id not in user_logs:
        user_logs[user_id] = deque(maxlen=100)
    user_logs[user_id].append(msg)
    socketio.emit("log_update", msg, room=user_id)


# ---------------- SocketIO client sync ----------------
@socketio.on('connect')
def handle_connect():
    user_id = session["user_id"]
    join_room(user_id)
    for msg in user_logs.get(user_id, []):
        emit("log_update", msg, room=user_id)


# ---------------- Run Flask server ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
