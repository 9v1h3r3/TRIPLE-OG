# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session
import threading
import time
import os
import json
from bot_runner import RenderBot

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "render-bot-secret-key-2024")

# Global bot instance
bot_instance = None
bot_status = {
    "is_running": False,
    "messages_sent": 0,
    "status": "Not Started",
    "last_active": None
}

@app.route('/')
def home():
    """Home page with bot controls"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get bot status"""
    return jsonify(bot_status)

@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    global bot_instance, bot_status
    
    if bot_status['is_running']:
        return jsonify({"success": False, "message": "Bot already running"})
    
    try:
        # Get parameters from request
        data = request.json
        delay = data.get('delay', 20)
        message_count = data.get('message_count', 10)
        
        # Initialize bot
        bot_instance = RenderBot()
        
        # Start bot in background thread
        bot_thread = threading.Thread(
            target=run_bot_async,
            args=(bot_instance, delay, message_count),
            daemon=True
        )
        bot_thread.start()
        
        bot_status.update({
            "is_running": True,
            "status": "Starting...",
            "last_active": time.strftime("%Y-%m-%d %H:%M:%S"),
            "delay": delay,
            "message_count": message_count
        })
        
        return jsonify({
            "success": True, 
            "message": "Bot started successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    global bot_instance, bot_status
    
    if bot_instance:
        bot_instance.stop()
    
    bot_status.update({
        "is_running": False,
        "status": "Stopped",
        "last_active": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    return jsonify({"success": True, "message": "Bot stopped"})

@app.route('/api/messages', methods=['GET', 'POST'])
def manage_messages():
    """Manage messages"""
    if request.method == 'GET':
        # Read messages
        try:
            with open('data/messages.txt', 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
            return jsonify({"success": True, "messages": messages})
        except:
            return jsonify({"success": False, "messages": []})
    
    else:  # POST
        # Add new message
        data = request.json
        new_message = data.get('message', '').strip()
        
        if new_message:
            try:
                with open('data/messages.txt', 'a', encoding='utf-8') as f:
                    f.write(new_message + '\n')
                return jsonify({"success": True, "message": "Message added"})
            except Exception as e:
                return jsonify({"success": False, "message": str(e)})
        
        return jsonify({"success": False, "message": "Empty message"})

def run_bot_async(bot, delay, message_count):
    """Run bot in background thread"""
    global bot_status
    
    try:
        bot_status['status'] = 'Running...'
        bot.run_automated_messaging(delay, message_count)
        
        # Update status when done
        bot_status.update({
            'is_running': False,
            'status': 'Completed',
            'messages_sent': bot.messages_sent,
            'last_active': time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        bot_status.update({
            'is_running': False,
            'status': f'Error: {str(e)}',
            'last_active': time.strftime("%Y-%m-%d %H:%M:%S")
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
