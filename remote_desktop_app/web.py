"""
Web interface for the remote desktop system
"""
import json
import os
from aiohttp import web
from aiohttp.web import Application, Response
from models import SystemConfig


class WebInterface:
    """Enterprise-grade web interface with responsive design"""
    def __init__(self, config: SystemConfig):
        self.config = config
        self.html_content = self._generate_html()

    def _generate_html(self) -> str:
        """Generate responsive HTML interface"""
        # Get the WebSocket port from the configuration
        ws_port = self.config.server.ws_port
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enterprise Remote Desktop</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                :root {{
                    --primary-color: #2c3e50;
                    --secondary-color: #3498db;
                    --success-color: #27ae60;
                    --danger-color: #e74c3c;
                    --dark-color: #1a1a1a;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    overflow: hidden;
                }}
                
                .main-header {{
                    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                    color: white;
                    padding: 1rem;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                .screen-container {{
                    position: relative;
                    background-color: var(--dark-color);
                    overflow: hidden;
                    height: calc(100vh - 120px);
                }}
                
                #screen {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    cursor: crosshair;
                }}
                
                .control-panel {{
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    padding: 1.5rem;
                    height: calc(100vh - 140px);
                    overflow-y: auto;
                }}
                
                .status-indicator {{
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }}
                
                .status-connected {{
                    background-color: var(--success-color);
                    box-shadow: 0 0 10px var(--success-color);
                }}
                
                .status-disconnected {{
                    background-color: var(--danger-color);
                }}
                
                .log-container {{
                    background-color: #2c3e50;
                    color: #ecf0f1;
                    border-radius: 8px;
                    padding: 1rem;
                    height: 200px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 0.85rem;
                }}
                
                .log-entry {{
                    margin-bottom: 0.5rem;
                    padding: 0.25rem;
                    border-left: 3px solid transparent;
                }}
                
                .log-entry.key {{ border-left-color: var(--success-color); }}
                .log-entry.click {{ border-left-color: var(--secondary-color); }}
                .log-entry.scroll {{ border-left-color: #9b59b6; }}
                .log-entry.move {{ border-left-color: #f39c12; }}
                .log-entry.system {{ border-left-color: #95a5a6; }}
                
                .metric-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }}
                
                .btn-custom {{
                    border-radius: 25px;
                    padding: 0.5rem 1.5rem;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }}
                
                .btn-custom:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }}
                
                .quality-slider {{
                    width: 100%;
                }}
                
                @media (max-width: 768px) {{
                    .control-panel {{
                        height: auto;
                        max-height: 300px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="main-header">
                <div class="container-fluid">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h1 class="h3 mb-0"><i class="fas fa-desktop me-2"></i>Enterprise Remote Desktop</h1>
                        </div>
                        <div class="col-md-6 text-end">
                            <div class="d-inline-block me-3">
                                <span class="status-indicator status-disconnected" id="status-indicator"></span>
                                <span id="connection-status">Disconnected</span>
                            </div>
                            <div class="d-inline-block">
                                <small>Latency: <span id="latency-info">--</span> ms</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="container-fluid mt-3">
                <div class="row">
                    <div class="col-lg-9">
                        <div class="screen-container">
                            <img id="screen" src="" alt="Remote Screen">
                        </div>
                    </div>
                    <div class="col-lg-3">
                        <div class="control-panel">
                            <!-- Connection Status -->
                            <div class="metric-card">
                                <h5><i class="fas fa-network-wired me-2"></i>Connection Status</h5>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span id="connection-detail">Not Connected</span>
                                    <button class="btn btn-light btn-sm" id="reconnect-btn">
                                        <i class="fas fa-sync-alt"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Performance Metrics -->
                            <div class="mb-4">
                                <h5><i class="fas fa-tachometer-alt me-2"></i>Performance</h5>
                                <div class="mb-3">
                                    <label class="form-label">Image Quality</label>
                                    <input type="range" class="form-range quality-slider" id="quality-slider" 
                                           min="30" max="95" value="75" step="5">
                                    <div class="d-flex justify-content-between">
                                        <small>Low</small>
                                        <small id="quality-value">75%</small>
                                        <small>High</small>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Frame Rate</label>
                                    <select class="form-select" id="fps-select">
                                        <option value="15">15 FPS (Low)</option>
                                        <option value="30" selected>30 FPS (Medium)</option>
                                        <option value="60">60 FPS (High)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <!-- Controls -->
                            <div class="mb-4">
                                <h5><i class="fas fa-mouse-pointer me-2"></i>Controls</h5>
                                <div class="d-grid gap-2">
                                    <button class="btn btn-primary btn-custom" id="left-click-btn">
                                        <i class="fas fa-mouse-pointer me-2"></i>Left Click
                                    </button>
                                    <button class="btn btn-secondary btn-custom" id="right-click-btn">
                                        <i class="fas fa-mouse-pointer me-2"></i>Right Click
                                    </button>
                                    <button class="btn btn-success btn-custom" id="auto-click-btn">
                                        <i class="fas fa-robot me-2"></i>Auto Click
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Event Log -->
                            <div>
                                <h5><i class="fas fa-list me-2"></i>Event Log</h5>
                                <div class="log-container" id="event-log">
                                    <div class="log-entry system">System initialized...</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Enterprise-grade JavaScript implementation
                class RemoteDesktopClient {{
                    constructor() {{
                        this.ws = null;
                        this.connected = false;
                        this.screenWidth = 1920;
                        this.screenHeight = 1080;
                        this.lastPingTime = 0;
                        this.autoClickActive = false;
                        this.wsPort = {ws_port}; // Use the configured WebSocket port
                        this.initializeComponents();
                        this.setupEventListeners();
                        this.connectWebSocket();
                    }}
                    
                    initializeComponents() {{
                        this.screenImg = document.getElementById('screen');
                        this.connectionStatus = document.getElementById('connection-status');
                        this.statusIndicator = document.getElementById('status-indicator');
                        this.latencyInfo = document.getElementById('latency-info');
                        this.eventLog = document.getElementById('event-log');
                        this.qualitySlider = document.getElementById('quality-slider');
                        this.qualityValue = document.getElementById('quality-value');
                        this.fpsSelect = document.getElementById('fps-select');
                    }}
                    
                    setupEventListeners() {{
                        // Screen interactions
                        this.screenImg.addEventListener('contextmenu', e => e.preventDefault());
                        this.screenImg.addEventListener('mousedown', this.handleMouseDown.bind(this));
                        this.screenImg.addEventListener('dblclick', this.handleDoubleClick.bind(this));
                        this.screenImg.addEventListener('mousemove', this.handleMouseMove.bind(this));
                        this.screenImg.addEventListener('wheel', this.handleWheel.bind(this));
                        
                        // Keyboard events
                        document.addEventListener('keydown', this.handleKeyDown.bind(this));
                        
                        // Control buttons
                        document.getElementById('left-click-btn').addEventListener('click', () => this.sendClick('left'));
                        document.getElementById('right-click-btn').addEventListener('click', () => this.sendClick('right'));
                        document.getElementById('auto-click-btn').addEventListener('click', this.toggleAutoClick.bind(this));
                        document.getElementById('reconnect-btn').addEventListener('click', () => this.connectWebSocket());
                        
                        // Performance controls
                        this.qualitySlider.addEventListener('input', this.updateQuality.bind(this));
                        this.fpsSelect.addEventListener('change', this.updateFPS.bind(this));
                    }}
                    
                    connectWebSocket() {{
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${{protocol}}//${{window.location.hostname}}:${{this.wsPort}}`;
                        
                        this.ws = new WebSocket(wsUrl);
                        this.ws.binaryType = 'arraybuffer';
                        
                        this.ws.onopen = () => {{
                            this.connected = true;
                            this.updateConnectionStatus('Connected', true);
                            this.startLatencyCheck();
                        }};
                        
                        this.ws.onmessage = (event) => {{
                            if (event.data instanceof ArrayBuffer) {{
                                this.handleFrameData(event.data);
                            }} else {{
                                this.handleJsonMessage(JSON.parse(event.data));
                            }}
                        }};
                        
                        this.ws.onclose = () => {{
                            this.connected = false;
                            this.updateConnectionStatus('Disconnected', false);
                            setTimeout(() => this.connectWebSocket(), 2000);
                        }};
                        
                        this.ws.onerror = (error) => {{
                            console.error('WebSocket Error:', error);
                        }};
                    }}
                    
                    handleFrameData(arrayBuffer) {{
                        const blob = new Blob([arrayBuffer], {{ type: 'image/jpeg' }});
                        const url = URL.createObjectURL(blob);
                        
                        this.screenImg.src = url;
                        //console.log(this.screenImg.src)

                        if (this.screenImg.currentSrc) {{
                            URL.revokeObjectURL(this.screenImg.currentSrc);
                        }}
                    }}
                    
                    handleJsonMessage(data) {{
                        if (data.type === 'pong') {{
                            const latency = Math.round(performance.now() - this.lastPingTime);
                            this.latencyInfo.textContent = latency;
                        }} else if (data.type === 'screen_size') {{
                            this.screenWidth = data.width;
                            this.screenHeight = data.height;
                        }} else {{
                            this.addLogEntry(data);
                        }}
                    }}

                    handleMouseDown(e) {{
                        e.preventDefault();
                        const coords = this.getScreenCoordinates(e);
                        const button = e.button === 0 ? 'left' : 'right';

                        this.sendCommand({{
                            type: 'control',
                            action: 'click',
                            x: coords.x,
                            y: coords.y,
                            button: button
                        }});
                    }}

                    handleDoubleClick(e) {{
                        e.preventDefault();
                        const coords = this.getScreenCoordinates(e);

                        this.sendCommand({{
                            type: 'control',
                            action: 'double_click',
                            x: coords.x,
                            y: coords.y
                        }});
                    }}

                    handleMouseMove(e) {{
                        const coords = this.getScreenCoordinates(e);

                        if (!this.lastMoveTime || Date.now() - this.lastMoveTime > 50) {{
                            this.lastMoveTime = Date.now();
                            this.sendCommand({{
                                type: 'control',
                                action: 'move',
                                x: coords.x,
                                y: coords.y
                            }});
                        }}
                    }}

                    handleWheel(e) {{
                        e.preventDefault();
                        const coords = this.getScreenCoordinates(e);
                        const deltaY = e.deltaY > 0 ? 1 : -1;

                        this.sendCommand({{
                            type: 'control',
                            action: 'scroll',
                            x: coords.x,
                            y: coords.y,
                            dy: deltaY
                        }});
                    }}

                    handleKeyDown(e) {{
                        if (e.key.toLowerCase() === 'end') {{
                            e.preventDefault();
                            return;
                        }}

                        this.sendCommand({{
                            type: 'control',
                            action: 'key',
                            key: e.key
                        }});
                    }}

                    getScreenCoordinates(e) {{
                        const rect = this.screenImg.getBoundingClientRect();
                        const scaleX = this.screenWidth / rect.width;
                        const scaleY = this.screenHeight / rect.height;

                        return {{
                            x: Math.round((e.clientX - rect.left) * scaleX),
                            y: Math.round((e.clientY - rect.top) * scaleY)
                        }};
                    }}

                    sendCommand(command) {{
                        if (this.connected) {{
                            this.ws.send(JSON.stringify(command));
                        }}
                    }}

                    sendClick(button) {{
                        this.sendCommand({{
                            type: 'control',
                            action: 'click',
                            button: button
                        }});
                    }}

                    toggleAutoClick() {{
                        this.autoClickActive = !this.autoClickActive;
                        const btn = document.getElementById('auto-click-btn');

                        if (this.autoClickActive) {{
                            btn.classList.remove('btn-success');
                            btn.classList.add('btn-danger');
                            btn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Auto Click';
                            this.sendCommand({{ type: 'command', action: 'start_auto_click' }});
                        }} else {{
                            btn.classList.remove('btn-danger');
                            btn.classList.add('btn-success');
                            btn.innerHTML = '<i class="fas fa-robot me-2"></i>Auto Click';
                            this.sendCommand({{ type: 'command', action: 'stop_auto_click' }});
                        }}
                    }}

                    updateQuality() {{
                        const quality = this.qualitySlider.value;
                        this.qualityValue.textContent = quality + '%';
                        this.sendCommand({{
                            type: 'command',
                            action: 'set_quality',
                            quality: parseInt(quality)
                        }});
                    }}

                    updateFPS() {{
                        const fps = this.fpsSelect.value;
                        this.sendCommand({{
                            type: 'command',
                            action: 'set_fps',
                            fps: parseInt(fps)
                        }});
                    }}

                    updateConnectionStatus(status, connected) {{
                        this.connectionStatus.textContent = status;
                        this.statusIndicator.className = `status-indicator ${{connected ? 'status-connected' : 'status-disconnected'}}`;
                    }}

                    addLogEntry(data) {{
                        const entry = document.createElement('div');
                        entry.className = `log-entry ${{data.type}}`;
                        entry.textContent = `[${{data.timestamp}}] ${{data.type.toUpperCase()}}: ${{JSON.stringify(data.details)}}`;

                        this.eventLog.appendChild(entry);
                        this.eventLog.scrollTop = this.eventLog.scrollHeight;

                        // Keep only last 100 entries
                        while (this.eventLog.childNodes.length > 100) {{
                            this.eventLog.removeChild(this.eventLog.firstChild);
                        }}
                    }}

                    startLatencyCheck() {{
                        setInterval(() => {{
                            if (this.connected) {{
                                this.lastPingTime = performance.now();
                                this.sendCommand({{ type: 'ping' }});
                            }}
                        }}, 2000);
                    }}
                }}

                // Initialize the application
                document.addEventListener('DOMContentLoaded', () => {{
                    new RemoteDesktopClient();
                }});
            </script>
        </body>
        </html>
        """

    async def handle_http_request(self, request: web.Request) -> Response:
        """Handle HTTP requests"""
        return Response(text=self.html_content, content_type='text/html')

    async def handle_file(self, request: web.Request) -> Response:
        """Handle file transfer requests"""
        # Basic file transfer implementation
        try:
            file_path = request.query.get('path', '')
            if not file_path or not os.path.exists(file_path):
                return Response(text="File not found", status=404)

            with open(file_path, 'rb') as f:
                content = f.read()

            # Get file extension for content type
            ext = os.path.splitext(file_path)[1].lower()
            content_type = {
                '.txt': 'text/plain',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.pdf': 'application/pdf',
                '.zip': 'application/zip',
            }.get(ext, 'application/octet-stream')

            return Response(body=content, content_type=content_type)
        except Exception as e:
            print(f"File transfer error: {e}")
            return Response(text="Error retrieving file", status=500)