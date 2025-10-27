<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Messenger Bot - Render</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>🤖 Facebook Messenger Bot</h1>
        <p class="subtitle">Deployed on Render Cloud</p>
        
        <div class="status-card">
            <h3>Bot Status</h3>
            <div id="status">Loading...</div>
            <div class="stats">
                <span id="messagesSent">0 messages sent</span>
                <span id="lastActive">Never</span>
            </div>
        </div>

        <div class="control-panel">
            <h3>Control Panel</h3>
            
            <div class="form-group">
                <label>Delay between messages (seconds):</label>
                <input type="number" id="delay" value="20" min="10" max="60">
            </div>
            
            <div class="form-group">
                <label>Maximum messages to send:</label>
                <input type="number" id="messageCount" value="10" min="1" max="50">
            </div>
            
            <div class="button-group">
                <button onclick="startBot()" id="startBtn" class="btn btn-success">🚀 Start Bot</button>
                <button onclick="stopBot()" id="stopBtn" class="btn btn-danger">🛑 Stop Bot</button>
            </div>
        </div>

        <div class="messages-panel">
            <h3>Message Management</h3>
            
            <div class="form-group">
                <label>Add new message:</label>
                <input type="text" id="newMessage" placeholder="Enter your message...">
                <button onclick="addMessage()" class="btn btn-primary">➕ Add Message</button>
            </div>
            
            <div id="messagesList" class="messages-list">
                Loading messages...
            </div>
        </div>

        <div class="logs-panel">
            <h3>Recent Logs</h3>
            <div id="logs" class="logs">
                <!-- Logs will appear here -->
            </div>
        </div>
    </div>

    <script>
        // Update status every 3 seconds
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').innerHTML = 
                        data.is_running ? 
                        '<span class="status-running">🟢 Running</span>' : 
                        '<span class="status-stopped">🔴 Stopped</span>';
                    
                    document.getElementById('messagesSent').textContent = 
                        `${data.messages_sent || 0} messages sent`;
                    document.getElementById('lastActive').textContent = 
                        `Last active: ${data.last_active || 'Never'}`;
                    
                    // Update button states
                    document.getElementById('startBtn').disabled = data.is_running;
                    document.getElementById('stopBtn').disabled = !data.is_running;
                });
        }

        // Start bot
        function startBot() {
            const delay = document.getElementById('delay').value;
            const messageCount = document.getElementById('messageCount').value;
            
            fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({delay: parseInt(delay), message_count: parseInt(messageCount)})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                updateStatus();
            });
        }

        // Stop bot
        function stopBot() {
            fetch('/api/stop', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    updateStatus();
                });
        }

        // Load messages
        function loadMessages() {
            fetch('/api/messages')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const messagesHtml = data.messages.map((msg, index) => 
                            `<div class="message-item">${index + 1}. ${msg}</div>`
                        ).join('');
                        document.getElementById('messagesList').innerHTML = messagesHtml;
                    }
                });
        }

        // Add new message
        function addMessage() {
            const newMessage = document.getElementById('newMessage').value;
            if (!newMessage.trim()) {
                alert('Please enter a message');
                return;
            }

            fetch('/api/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: newMessage})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                document.getElementById('newMessage').value = '';
                loadMessages();
            });
        }

        // Initialize
        setInterval(updateStatus, 3000);
        updateStatus();
        loadMessages();
    </script>
</body>
</html>
