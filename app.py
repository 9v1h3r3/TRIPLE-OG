import eventlet
eventlet.monkey_patch()  # MUST be first

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import asyncio, threading, json, random, traceback
from collections import deque
from playwright.async_api import async_playwright
import uuid

app = Flask(__name__)
app.secret_key = "SUPERSECRET_KEY"
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

user_tasks = {}
user_logs = {}
user_progress = {}

# ---------- helpers ----------
def emit_log(user_id, msg):
    if user_id not in user_logs:
        user_logs[user_id] = deque(maxlen=500)
    user_logs[user_id].append(msg)
    socketio.emit("log_update", msg, room=user_id)

def safe_emit(user_id, event, data):
    try:
        socketio.emit(event, data, room=user_id)
    except:
        pass

# ---------- session id ----------
@app.before_request
def assign_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())

# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    user_id = session["user_id"]
    if user_id in user_tasks:
        return "⚠️ Bot already running!"

    try:
        cookie_json = request.form["cookie"]
        prefix = request.form.get("prefix", "").strip()
        targets = [t.strip() for t in request.form["targets"].splitlines() if t.strip()]
        msg_file = request.files["messages"]
        messages = [m.strip() for m in msg_file.read().decode().splitlines() if m.strip()]
    except Exception as e:
        return f"❌ Invalid form: {e}"

    if not targets or not messages:
        return "❌ Please provide thread IDs and a message file."

    # init status
    user_logs[user_id] = deque(maxlen=500)
    user_progress[user_id] = {"sent": 0, "total": len(messages) * len(targets), "logged_in_as": None}

    # start background loop
    loop = asyncio.new_event_loop()
    task = loop.create_task(run_bot(user_id, cookie_json, prefix, targets, messages))
    user_tasks[user_id] = task

    def run_loop(loop, task):
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        except Exception:
            emit_log(user_id, f"Fatal background error:\n{traceback.format_exc()}")
        finally:
            try:
                loop.close()
            except:
                pass

    threading.Thread(target=run_loop, args=(loop, task), daemon=True).start()
    return "✅ Bot started (login verification will run first)."

@app.route("/stop", methods=["POST"])
def stop():
    user_id = session["user_id"]
    if user_id in user_tasks:
        try:
            task = user_tasks.pop(user_id)
            task.cancel()
            emit_log(user_id, "⛔ Stop signal sent. Bot will stop soon.")
            safe_emit(user_id, "login_status", {"status": "stopped"})
            return "Bot stopped"
        except Exception as e:
            return f"Error stopping: {e}"
    return "No bot running"

# ---------- core logic ----------
async def run_bot(user_id, cookie_json, prefix, targets, messages):
    # parse cookies
    try:
        cookies = json.loads(cookie_json)
    except Exception as e:
        emit_log(user_id, f"❌ Invalid cookie JSON: {e}")
        safe_emit(user_id, "login_status", {"status": "invalid_cookies"})
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            # add cookies
            try:
                await context.add_cookies(cookies)
            except Exception as e:
                emit_log(user_id, f"⚠️ Warning: add_cookies failed: {e}")

            page = await context.new_page()

            # 1) Login check
            try:
                await page.goto("https://www.facebook.com/", timeout=60000)
                await page.wait_for_load_state("networkidle", timeout=30000)
            except:
                # still continue — we'll try to detect login below
                pass

            # detect if logged in
            is_logged_in = True
            try:
                # quick check: login form present?
                login_form = await page.query_selector('input[name="email"], input#email')
                if login_form:
                    is_logged_in = False
                # also if URL contains "login"
                if "login" in page.url.lower():
                    is_logged_in = False
            except:
                pass

            username = None
            if is_logged_in:
                # attempt to get profile name from title or meta
                try:
                    title = await page.title()
                    if title and "Facebook" not in title:
                        username = title
                    else:
                        # try reading profile link text (best-effort)
                        try:
                            el = await page.query_selector('a[aria-label^="Profile"], a[title]')
                            if el:
                                username = await el.inner_text()
                        except:
                            pass
                except:
                    pass

            if not is_logged_in:
                emit_log(user_id, "❌ Login failed with provided cookies. Stopping.")
                safe_emit(user_id, "login_status", {"status": "failed", "username": None})
                await browser.close()
                return
            else:
                emit_log(user_id, f"✅ Logged in (detected): {username or 'Unknown user'}")
                user_progress[user_id]["logged_in_as"] = username or "Unknown"
                safe_emit(user_id, "login_status", {"status": "ok", "username": username or "Unknown"})

            # 2) message sending loop
            total = user_progress[user_id]["total"]
            sent = 0

            for tid in targets:
                # open thread (try e2ee and normal)
                thread_urls = [
                    f"https://www.facebook.com/messages/e2ee/t/{tid}",
                    f"https://www.facebook.com/messages/t/{tid}",
                    f"https://m.facebook.com/messages/t/{tid}"
                ]
                opened = False
                for url in thread_urls:
                    try:
                        emit_log(user_id, f"➡️ Opening: {url}")
                        await page.goto(url, timeout=60000)
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        # small pause to let box appear
                        await asyncio.sleep(2)
                        # quick check for presence of message box
                        sel = await find_input_selector(page)
                        if sel:
                            opened = True
                            break
                    except Exception as e:
                        # try next url
                        continue

                if not opened:
                    emit_log(user_id, f"[!] Could not open thread {tid} (skipping).")
                    continue

                # send messages for this thread
                for msg in messages:
                    try:
                        full_text = f"{prefix} {msg}".strip()
                        ok = await send_with_retries(page, tid, full_text, user_id)
                        if ok:
                            sent += 1
                            user_progress[user_id]["sent"] = sent
                            safe_emit(user_id, "progress_update", user_progress[user_id])
                        # wait 5-10 seconds between sends
                        await asyncio.sleep(random.uniform(5, 10))
                    except asyncio.CancelledError:
                        emit_log(user_id, "⛔ Bot cancelled by user")
                        await browser.close()
                        return
                    except Exception as e:
                        emit_log(user_id, f"[x] Error while handling message in {tid}: {e}")

            await browser.close()
            emit_log(user_id, "✅ Completed all threads.")
            safe_emit(user_id, "login_status", {"status": "done", "username": user_progress[user_id].get("logged_in_as")})

    except Exception as e:
        emit_log(user_id, f"⚠️ Fatal error:\n{traceback.format_exc()}")
        safe_emit(user_id, "login_status", {"status": "error"})

# ---------- helper functions for page actions ----------
async def find_input_selector(page):
    """Return first working selector string or None."""
    candidates = [
        'div[aria-label="Message"]',
        'div[contenteditable="true"]',
        'div[role="textbox"]',
        'div[aria-label="Type a message..."]',
        'textarea[name="message"]',
        'div[aria-label="New message"]'
    ]
    for sel in candidates:
        try:
            el = await page.query_selector(sel)
            if el:
                return sel
        except:
            continue
    return None

async def send_with_retries(page, tid, text, user_id, max_retries=3):
    selectors = [
        'div[aria-label="Message"]',
        'div[contenteditable="true"]',
        'div[role="textbox"]',
        'div[aria-label="Type a message..."]',
        'textarea[name="message"]'
    ]
    for attempt in range(1, max_retries + 1):
        try:
            sel = None
            for s in selectors:
                try:
                    await page.wait_for_selector(s, timeout=8000)
                    el = await page.query_selector(s)
                    if el:
                        sel = s
                        input_box = el
                        break
                except:
                    continue

            if not sel:
                emit_log(user_id, f"[!] Input box missing for {tid} (attempt {attempt}/{max_retries}) — reloading")
                await page.reload()
                await asyncio.sleep(4)
                continue

            # paste text into contentEditable or textarea
            await input_box.click()
            # set innerText for contenteditable, value for textarea
            await page.evaluate(
                """(sel, txt) => {
                    const el = document.querySelector(sel) || document.activeElement;
                    if (!el) return;
                    if (el.isContentEditable) {
                        // set plain text preserving line breaks
                        el.innerText = txt;
                        // also set textContent in some layouts
                        el.textContent = txt;
                    } else if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                        el.value = txt;
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                    } else {
                        // fallback to activeElement
                        if (document.activeElement && document.activeElement.isContentEditable) {
                            document.activeElement.innerText = txt;
                        }
                    }
                }""",
                sel, text
            )

            # dispatch Enter key as safe keyboard event
            await page.evaluate(
                """() => {
                    const ev = new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', bubbles: true});
                    const ev2 = new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', bubbles: true});
                    const el = document.activeElement;
                    if (el) {
                        el.dispatchEvent(ev);
                        el.dispatchEvent(ev2);
                    }
                }"""
            )

            emit_log(user_id, f"💬 Sent to {tid}: {text[:80]}...")
            return True

        except Exception as e:
            emit_log(user_id, f"[x] Error sending to {tid} (attempt {attempt}): {e}")
            await asyncio.sleep(2)
            continue

    emit_log(user_id, f"❌ Failed to send to {tid} after {max_retries} attempts.")
    return False

# ---------- socket events ----------
@socketio.on("connect")
def on_connect():
    user_id = session["user_id"]
    join_room(user_id)
    # send last logs
    for msg in user_logs.get(user_id, []):
        emit("log_update", msg, room=user_id)
    # send progress if exists
    if user_id in user_progress:
        emit("progress_update", user_progress[user_id], room=user_id)
        emit("login_status", {"status": "ready", "username": user_progress[user_id].get("logged_in_as")}, room=user_id)

# ---------- run ----------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
