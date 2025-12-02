// Basic Remote Desk Server (No External Dependencies)
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;

// In-memory storage
let activeSessions = {};
let connectedClients = {};
let desktopData = {
  screenResolution: { width: 1920, height: 1080 },
  mousePosition: { x: 0, y: 0 },
  clipboard: '',
  connectedDevices: 0
};

// Create public directory and files if they don't exist
const publicDir = path.join(__dirname, 'public');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir);
}

// Create main HTML page
const mainHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remote Desk - Control Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .status-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .status-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #667eea;
        }
        .controls {
            margin-top: 20px;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .btn-danger {
            background: #e74c3c;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-success {
            background: #2ecc71;
        }
        .btn-success:hover {
            background: #27ae60;
        }
        .connection-status {
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            text-align: center;
        }
        .connected {
            background: #d4edda;
            color: #155724;
        }
        .disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        .file-transfer {
            margin-top: 20px;
        }
        .file-input {
            margin: 10px 0;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Remote Desk Control Panel</h1>
            <p>Secure remote desktop access and control</p>
        </header>
        
        <div class="connection-status disconnected" id="connectionStatus">
            Disconnected from server
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h2>System Status</h2>
                <div class="status-grid" id="statusGrid">
                    <div class="status-item">
                        <div class="status-value" id="connectedDevices">0</div>
                        <div>Connected Devices</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="activeSessions">0</div>
                        <div>Active Sessions</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="resolution">-</div>
                        <div>Resolution</div>
                    </div>
                    <div class="status-item">
                        <div class="status-value" id="mousePos">0,0</div>
                        <div>Mouse Position</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Desktop Controls</h2>
                <div class="controls">
                    <button class="btn" onclick="sendControl('mouse', {position: {x: 100, y: 100}})">Move Mouse</button>
                    <button class="btn" onclick="sendControl('keyboard', {key: 'Ctrl+Alt+Del'})">Send Key Combo</button>
                    <button class="btn" onclick="sendControl('clipboard', {content: 'Hello from remote desk!'})">Set Clipboard</button>
                    <button class="btn btn-danger" onclick="sendControl('screen', {resolution: {width: 1920, height: 1080}})">Reset Resolution</button>
                </div>
                
                <div class="file-transfer">
                    <h3>File Transfer</h3>
                    <input type="file" id="fileInput" class="file-input">
                    <button class="btn" onclick="sendFile()">Upload File</button>
                </div>
            </div>
            
            <div class="card">
                <h2>Session Management</h2>
                <div class="controls">
                    <button class="btn btn-success" onclick="startSession()">Start Session</button>
                    <button class="btn btn-danger" onclick="endSession()">End Session</button>
                    <button class="btn" onclick="refreshStatus()">Refresh Status</button>
                </div>
                <div id="sessionList" style="margin-top: 15px;">
                    <p>No active sessions</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function sendControl(action, data) {
            fetch('/api/desktop/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer demo-token'
                },
                body: JSON.stringify({ action, data })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    console.log('Control sent:', action);
                    alert('Control command sent successfully!');
                } else {
                    console.error('Error sending control:', result.error);
                    alert('Error sending control: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error connecting to server');
            });
        }
        
        function startSession() {
            // Simulate starting a session
            alert('Session started!');
        }
        
        function endSession() {
            // Simulate ending a session
            alert('Session ended!');
        }
        
        function refreshStatus() {
            fetch('/api/desktop/info', {
                headers: {
                    'Authorization': 'Bearer demo-token'
                }
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('connectedDevices').textContent = 1; // Simulated
                document.getElementById('resolution').textContent = data.screenResolution.width + 'x' + data.screenResolution.height;
                document.getElementById('mousePos').textContent = data.mousePosition.x + ',' + data.mousePosition.y;
            })
            .catch(error => console.error('Error fetching status:', error));
        }
        
        function sendFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file first');
                return;
            }
            
            alert('File transfer would start in a full implementation: ' + file.name);
        }
    </script>
</body>
</html>
`;

const adminHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remote Desk - Admin Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 1rem;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 {
            color: #e74c3c;
            margin-bottom: 15px;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #e74c3c;
        }
        .stat-label {
            font-size: 1rem;
            color: #666;
            margin-top: 5px;
        }
        .log-entry {
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .log-entry.info {
            border-left: 3px solid #3498db;
        }
        .log-entry.warning {
            border-left: 3px solid #f39c12;
        }
        .log-entry.error {
            border-left: 3px solid #e74c3c;
        }
        .btn {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #c0392b;
        }
        .btn-secondary {
            background: #3498db;
        }
        .btn-secondary:hover {
            background: #2980b9;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        .action-cell {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Remote Desk - Admin Panel</h1>
            <p>Administrative controls and monitoring</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="totalConnections">125</div>
                <div class="stat-label">Total Connections</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="activeSessionsCount">5</div>
                <div class="stat-label">Active Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="connectedDevicesCount">8</div>
                <div class="stat-label">Connected Devices</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="uptime">48h 12m</div>
                <div class="stat-label">Server Uptime</div>
            </div>
        </div>
        
        <div class="card">
            <h2>System Controls</h2>
            <button class="btn" onclick="restartServer()">Restart Server</button>
            <button class="btn btn-secondary" onclick="clearLogs()">Clear Logs</button>
            <button class="btn btn-secondary" onclick="backupConfig()">Backup Config</button>
        </div>
        
        <div class="card">
            <h2>Active Connections</h2>
            <table id="connectionsTable">
                <thead>
                    <tr>
                        <th>Session ID</th>
                        <th>Connected At</th>
                        <th>IP Address</th>
                        <th>Type</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="connectionsBody">
                    <tr>
                        <td>session_a1b2c3d4</td>
                        <td>2023-07-15 14:30:22</td>
                        <td>192.168.1.101</td>
                        <td>Web Client</td>
                        <td class="action-cell">
                            <button class="btn" onclick="disconnectSession(this)">Disconnect</button>
                        </td>
                    </tr>
                    <tr>
                        <td>session_e5f6g7h8</td>
                        <td>2023-07-15 15:45:11</td>
                        <td>10.0.0.55</td>
                        <td>Mobile App</td>
                        <td class="action-cell">
                            <button class="btn" onclick="disconnectSession(this)">Disconnect</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>System Logs</h2>
            <div id="logsContainer">
                <div class="log-entry info">[INFO] Server started at ${new Date().toISOString()}</div>
                <div class="log-entry info">[INFO] Listening on port ${PORT}</div>
                <div class="log-entry info">[INFO] New connection from 192.168.1.101</div>
                <div class="log-entry warning">[WARNING] High CPU usage detected</div>
                <div class="log-entry info">[INFO] Configuration updated</div>
            </div>
        </div>
    </div>

    <script>
        function restartServer() {
            if (confirm('Are you sure you want to restart the server? This will disconnect all users.')) {
                alert('Server restart initiated');
            }
        }
        
        function clearLogs() {
            const logsContainer = document.getElementById('logsContainer');
            logsContainer.innerHTML = '<div class="log-entry info">[INFO] Logs cleared at ' + new Date().toISOString() + '</div>';
        }
        
        function backupConfig() {
            alert('Configuration backed up successfully!');
        }
        
        function disconnectSession(button) {
            button.textContent = 'Disconnecting...';
            setTimeout(() => {
                button.textContent = 'Disconnected';
                button.style.backgroundColor = '#95a5a6';
                button.disabled = true;
            }, 1000);
        }
    </script>
</body>
</html>
`;

// Write HTML files
fs.writeFileSync(path.join(publicDir, 'index.html'), mainHtml);
fs.writeFileSync(path.join(publicDir, 'admin.html'), adminHtml);

// HTTP server
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  
  // Routing
  if (pathname === '/' || pathname === '/index.html') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(mainHtml);
  } 
  else if (pathname === '/admin') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(adminHtml);
  }
  else if (pathname === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      status: 'running', 
      timestamp: new Date().toISOString(),
      connectedClients: Object.keys(connectedClients).length,
      activeSessions: Object.keys(activeSessions).length
    }));
  }
  else if (pathname === '/api/desktop/info') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== 'demo-token')) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access token required' }));
      return;
    }
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(desktopData));
  }
  else if (pathname === '/api/desktop/control' && req.method === 'POST') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== 'demo-token')) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access token required' }));
      return;
    }
    
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      try {
        const { action, data } = JSON.parse(body);
        
        // Process the control action
        switch(action) {
          case 'mouse':
            desktopData.mousePosition = data.position || desktopData.mousePosition;
            break;
          case 'clipboard':
            desktopData.clipboard = data.content || desktopData.clipboard;
            break;
          case 'screen':
            desktopData.screenResolution = data.resolution || desktopData.screenResolution;
            break;
        }
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, action, data }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
  }
  else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`Remote Desk basic server running on port ${PORT}`);
  console.log(`Visit http://localhost:${PORT} to see your app`);
  console.log(`Visit http://localhost:${PORT}/admin for admin panel (use token: demo-token)`);
});