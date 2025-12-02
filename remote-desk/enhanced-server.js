// Enhanced Remote Desk Server with Additional Features
require('dotenv').config();
const http = require('http');
const https = require('https');
const url = require('url');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = process.env.PORT || 3000;
const ACCESS_TOKEN = process.env.ACCESS_TOKEN || 'demo-token';

// In-memory storage
let activeSessions = {};
let connectedClients = {};
let desktopData = {
  screenResolution: { width: 1920, height: 1080 },
  mousePosition: { x: 0, y: 0 },
  clipboard: '',
  connectedDevices: 0,
  systemStats: {
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
    networkUsage: 0
  }
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
        .btn-warning {
            background: #f39c12;
        }
        .btn-warning:hover {
            background: #e67e22;
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
        .monitoring-chart {
            height: 200px;
            background: #f8f9fa;
            border-radius: 6px;
            margin: 15px 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .session-list {
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }
        .session-item {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
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
                
                <h3>System Resources</h3>
                <div class="monitoring-chart">
                    <div>System resource monitoring would be displayed here</div>
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
                
                <h3>Power Controls</h3>
                <div class="controls">
                    <button class="btn btn-warning" onclick="sendControl('power', {action: 'lock'})">Lock Screen</button>
                    <button class="btn btn-warning" onclick="sendControl('power', {action: 'sleep'})">Sleep</button>
                    <button class="btn btn-danger" onclick="sendControl('power', {action: 'shutdown'})">Shutdown</button>
                </div>
                
                <div class="file-transfer">
                    <h3>File Transfer</h3>
                    <input type="file" id="fileInput" class="file-input">
                    <button class="btn" onclick="sendFile()">Upload File</button>
                    <button class="btn btn-success" onclick="downloadFile()">Download File</button>
                </div>
            </div>
            
            <div class="card">
                <h2>Session Management</h2>
                <div class="controls">
                    <button class="btn btn-success" onclick="startSession()">Start Session</button>
                    <button class="btn btn-danger" onclick="endSession()">End Session</button>
                    <button class="btn" onclick="refreshStatus()">Refresh Status</button>
                </div>
                
                <h3>Active Sessions</h3>
                <div id="sessionList" class="session-list">
                    <p>No active sessions</p>
                </div>
                
                <h3>Remote Commands</h3>
                <div class="controls">
                    <button class="btn" onclick="sendCommand('screenshot')">Take Screenshot</button>
                    <button class="btn" onclick="sendCommand('record')">Start Recording</button>
                    <button class="btn" onclick="sendCommand('list-processes')">List Processes</button>
                </div>
            </div>
        </div>
    </div>

    <footer>
        <p>Remote Desk v2.0 | Secure Remote Desktop Solution</p>
        <p>Server Status: <span id="serverStatus">Running</span> | Uptime: <span id="uptime">0h 0m</span></p>
    </footer>

    <script>
        function sendControl(action, data) {
            fetch('/api/desktop/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ${ACCESS_TOKEN}'
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
        
        function sendCommand(command) {
            fetch('/api/desktop/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ${ACCESS_TOKEN}'
                },
                body: JSON.stringify({ command })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    console.log('Command sent:', command);
                    alert('Command executed: ' + command);
                } else {
                    console.error('Error sending command:', result.error);
                    alert('Error executing command: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error connecting to server');
            });
        }
        
        function startSession() {
            fetch('/api/session/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ${ACCESS_TOKEN}'
                }
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('Session started successfully!');
                    refreshStatus();
                } else {
                    alert('Error starting session: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error connecting to server');
            });
        }
        
        function endSession() {
            fetch('/api/session/end', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ${ACCESS_TOKEN}'
                }
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('Session ended successfully!');
                    refreshStatus();
                } else {
                    alert('Error ending session: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error connecting to server');
            });
        }
        
        function refreshStatus() {
            fetch('/api/desktop/info', {
                headers: {
                    'Authorization': 'Bearer ${ACCESS_TOKEN}'
                }
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('connectedDevices').textContent = data.connectedDevices;
                document.getElementById('resolution').textContent = data.screenResolution.width + 'x' + data.screenResolution.height;
                document.getElementById('mousePos').textContent = data.mousePosition.x + ',' + data.mousePosition.y;
                
                // Update sessions list
                const sessionList = document.getElementById('sessionList');
                if (Object.keys(data.sessions || {}).length > 0) {
                    sessionList.innerHTML = '';
                    Object.keys(data.sessions).forEach(sessionId => {
                        const sessionItem = document.createElement('div');
                        sessionItem.className = 'session-item';
                        sessionItem.textContent = sessionId.substring(0, 8) + '... - ' + data.sessions[sessionId].type;
                        sessionList.appendChild(sessionItem);
                    });
                } else {
                    sessionList.innerHTML = '<p>No active sessions</p>';
                }
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
            
            alert('File transfer would start in a full implementation: ' + file.name + ' (' + (file.size / 1024 / 1024).toFixed(2) + ' MB)');
        }
        
        function downloadFile() {
            alert('File download would start in a full implementation');
        }
        
        // Initial status refresh
        refreshStatus();
        
        // Update status every 30 seconds
        setInterval(refreshStatus, 30000);
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
        .security-settings {
            margin-top: 20px;
        }
        .setting-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
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
            <button class="btn btn-secondary" onclick="updateSystem()">System Update</button>
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
                        <th>Location</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="connectionsBody">
                    <tr>
                        <td>session_a1b2c3d4</td>
                        <td>2023-07-15 14:30:22</td>
                        <td>192.168.1.101</td>
                        <td>Web Client</td>
                        <td>New York, US</td>
                        <td class="action-cell">
                            <button class="btn" onclick="disconnectSession(this)">Disconnect</button>
                        </td>
                    </tr>
                    <tr>
                        <td>session_e5f6g7h8</td>
                        <td>2023-07-15 15:45:11</td>
                        <td>10.0.0.55</td>
                        <td>Mobile App</td>
                        <td>London, UK</td>
                        <td class="action-cell">
                            <button class="btn" onclick="disconnectSession(this)">Disconnect</button>
                        </td>
                    </tr>
                    <tr>
                        <td>session_i9j0k1l2</td>
                        <td>2023-07-15 16:20:05</td>
                        <td>172.16.0.33</td>
                        <td>Desktop App</td>
                        <td>Tokyo, JP</td>
                        <td class="action-cell">
                            <button class="btn" onclick="disconnectSession(this)">Disconnect</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Security Settings</h2>
            <div class="security-settings">
                <div class="setting-row">
                    <span>Require Authentication:</span>
                    <input type="checkbox" id="authToggle" checked>
                </div>
                <div class="setting-row">
                    <span>Enable Session Recording:</span>
                    <input type="checkbox" id="recordingToggle">
                </div>
                <div class="setting-row">
                    <span>Allow File Transfer:</span>
                    <input type="checkbox" id="fileTransferToggle" checked>
                </div>
                <div class="setting-row">
                    <span>Session Timeout (min):</span>
                    <input type="number" id="timeoutInput" value="30" min="1" max="120">
                </div>
            </div>
            <button class="btn btn-secondary" onclick="saveSettings()" style="margin-top: 15px;">Save Settings</button>
        </div>
        
        <div class="card">
            <h2>System Logs</h2>
            <div id="logsContainer">
                <div class="log-entry info">[INFO] Server started at ${new Date().toISOString()}</div>
                <div class="log-entry info">[INFO] Listening on port ${PORT}</div>
                <div class="log-entry info">[INFO] New connection from 192.168.1.101</div>
                <div class="log-entry warning">[WARNING] High CPU usage detected (85%)</div>
                <div class="log-entry info">[INFO] Configuration updated</div>
                <div class="log-entry error">[ERROR] Failed authentication attempt from 10.0.0.25</div>
                <div class="log-entry info">[INFO] User session_abcdef12 ended</div>
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
        
        function updateSystem() {
            if (confirm('Are you sure you want to update the system? This may cause a brief service interruption.')) {
                alert('System update initiated');
            }
        }
        
        function disconnectSession(button) {
            button.textContent = 'Disconnecting...';
            setTimeout(() => {
                button.textContent = 'Disconnected';
                button.style.backgroundColor = '#95a5a6';
                button.disabled = true;
            }, 1000);
        }
        
        function saveSettings() {
            const settings = {
                authRequired: document.getElementById('authToggle').checked,
                recordingEnabled: document.getElementById('recordingToggle').checked,
                fileTransferEnabled: document.getElementById('fileTransferToggle').checked,
                sessionTimeout: document.getElementById('timeoutInput').value
            };
            
            alert('Settings saved successfully!');
            console.log('Settings:', settings);
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
      activeSessions: Object.keys(activeSessions).length,
      serverUptime: process.uptime(),
      version: '2.0.0'
    }));
  }
  else if (pathname === '/api/desktop/info') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== ACCESS_TOKEN)) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access token required' }));
      return;
    }
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      ...desktopData,
      sessions: activeSessions
    }));
  }
  else if (pathname === '/api/desktop/control' && req.method === 'POST') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== ACCESS_TOKEN)) {
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
          case 'power':
            console.log(`Power action: ${data.action}`);
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
  else if (pathname === '/api/desktop/command' && req.method === 'POST') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== ACCESS_TOKEN)) {
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
        const { command } = JSON.parse(body);
        
        // Process the command
        switch(command) {
          case 'screenshot':
            console.log('Taking screenshot...');
            break;
          case 'record':
            console.log('Starting recording...');
            break;
          case 'list-processes':
            console.log('Listing processes...');
            break;
        }
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, command, result: 'Command executed' }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
  }
  else if (pathname === '/api/session/start' && req.method === 'POST') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== ACCESS_TOKEN)) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access token required' }));
      return;
    }
    
    const sessionId = 'session_' + crypto.randomBytes(8).toString('hex');
    activeSessions[sessionId] = {
      id: sessionId,
      startedAt: new Date().toISOString(),
      type: 'remote-control',
      active: true
    };
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true, sessionId }));
  }
  else if (pathname === '/api/session/end' && req.method === 'POST') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== ACCESS_TOKEN)) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access token required' }));
      return;
    }
    
    // End the most recent session
    const sessionIds = Object.keys(activeSessions);
    if (sessionIds.length > 0) {
      const lastSessionId = sessionIds[sessionIds.length - 1];
      activeSessions[lastSessionId].active = false;
      activeSessions[lastSessionId].endedAt = new Date().toISOString();
    }
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true }));
  }
  else if (pathname === '/api/sessions') {
    // Check for auth header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token || (token !== ACCESS_TOKEN)) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Access token required' }));
      return;
    }
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ sessions: activeSessions }));
  }
  else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`Remote Desk enhanced server running on port ${PORT}`);
  console.log(`Visit http://localhost:${PORT} to see your app`);
  console.log(`Visit http://localhost:${PORT}/admin for admin panel (use token: ${ACCESS_TOKEN})`);
});