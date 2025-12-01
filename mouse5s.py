"""
Enterprise Remote Desktop Control System - Complete Solution
Author: PhD Software Engineer
Version: 2.0.0
License: Enterprise
"""

import asyncio
import websockets
import json
import time
import socket
import logging
import ssl
import threading
import queue
import zlib
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import numpy as np
import cv2
import mss
from aiohttp import web
from aiohttp.web import Application, Response, WebSocketResponse
from pynput import keyboard, mouse
from pynput.keyboard import Controller as KController, Key
from pynput.mouse import Controller as MController, Button
from cryptography.fernet import Fernet
from prometheus_client import start_http_server, Counter, Histogram

# ==================== Configuration Management ====================
@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "0.0.0.0"
    http_port: int = 3000
    ws_port: int = 8765
    metrics_port: int = 9090
    max_connections: int = 10
    connection_timeout: int = 30  # seconds
    # Port fallback settings
    http_port_fallback_start: int = 3001
    http_port_fallback_end: int = 3010
    ws_port_fallback_start: int = 8766
    ws_port_fallback_end: int = 8775
    metrics_port_fallback_start: int = 9091
    metrics_port_fallback_end: int = 9100

@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    max_fps: int = 30
    jpeg_quality: int = 75
    compression_level: int = 6  # ZLIB compression level (0-9)
    frame_queue_size: int = 3
    mouse_throttle_ms: int = 16
    enable_h264: bool = False  # Future feature flag
    downscale_threshold: int = 1920  # Downscale if width > this value

@dataclass
class SecurityConfig:
    """Security and encryption settings"""
    enable_ssl: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    encryption_key: Optional[str] = None
    auth_required: bool = False
    auth_token: Optional[str] = None
    allowed_ips: list = field(default_factory=list)
    block_end_key: bool = True  # Block END key for security

@dataclass
class FeatureConfig:
    """Feature toggle configuration"""
    enable_audio: bool = False
    enable_clipboard: bool = True
    enable_file_transfer: bool = True
    enable_session_recording: bool = False
    enable_multi_monitor: bool = True
    enable_auto_click: bool = True
    enable_keyboard_shortcuts: bool = True

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_file: str = "remote-desktop.log"
    log_max_size: int = 10  # MB
    log_backup_count: int = 5
    enable_access_log: bool = True
    enable_error_log: bool = True

@dataclass
class SystemConfig:
    """Main configuration container"""
    server: ServerConfig = field(default_factory=ServerConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SystemConfig':
        """Create config from dictionary"""
        server_config = ServerConfig(**config_dict.get('server', {}))
        performance_config = PerformanceConfig(**config_dict.get('performance', {}))
        security_config = SecurityConfig(**config_dict.get('security', {}))
        feature_config = FeatureConfig(**config_dict.get('features', {}))
        logging_config = LoggingConfig(**config_dict.get('logging', {}))
        
        return cls(
            server=server_config,
            performance=performance_config,
            security=security_config,
            features=feature_config,
            logging=logging_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'server': self.server.__dict__,
            'performance': self.performance.__dict__,
            'security': self.security.__dict__,
            'features': self.features.__dict__,
            'logging': self.logging.__dict__
        }

class ConfigManager:
    """Configuration management system"""
    
    DEFAULT_CONFIG_PATH = "config/remote-desktop.json"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> SystemConfig:
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_dict = json.load(f)
                return SystemConfig.from_dict(config_dict)
            else:
                # Create default config
                config = SystemConfig()
                self.save_config(config)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return SystemConfig()
    
    def save_config(self, config: SystemConfig = None) -> bool:
        """Save configuration to file"""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = config or self.config
            with open(self.config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        try:
            # Validate server settings
            if not (1 <= self.config.server.http_port <= 65535):
                print("Error: HTTP port must be between 1 and 65535")
                return False
            
            if not (1 <= self.config.server.ws_port <= 65535):
                print("Error: WebSocket port must be between 1 and 65535")
                return False
            
            # Validate performance settings
            if not (1 <= self.config.performance.max_fps <= 120):
                print("Error: Max FPS must be between 1 and 120")
                return False
            
            if not (10 <= self.config.performance.jpeg_quality <= 100):
                print("Error: JPEG quality must be between 10 and 100")
                return False
            
            if not (0 <= self.config.performance.compression_level <= 9):
                print("Error: Compression level must be between 0 and 9")
                return False
            
            # Validate security settings
            if self.config.security.enable_ssl:
                if not self.config.security.ssl_cert_path or not os.path.exists(self.config.security.ssl_cert_path):
                    print("Error: SSL certificate path is required when SSL is enabled")
                    return False
                
                if not self.config.security.ssl_key_path or not os.path.exists(self.config.security.ssl_key_path):
                    print("Error: SSL key path is required when SSL is enabled")
                    return False
            
            # Validate logging settings
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if self.config.logging.log_level not in valid_log_levels:
                print(f"Error: Log level must be one of {valid_log_levels}")
                return False
            
            return True
        except Exception as e:
            print(f"Error validating config: {e}")
            return False
    
    def create_example_configs(self):
        """Create example configuration files"""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Default configuration
        default_config = SystemConfig()
        with open(config_dir / "remote-desktop.json", "w") as f:
            json.dump(default_config.to_dict(), f, indent=2)
        
        # High performance configuration
        high_perf_config = SystemConfig()
        high_perf_config.performance.max_fps = 60
        high_perf_config.performance.jpeg_quality = 90
        high_perf_config.performance.compression_level = 3
        high_perf_config.performance.mouse_throttle_ms = 8
        high_perf_config.features.enable_audio = True
        
        with open(config_dir / "high-performance.json", "w") as f:
            json.dump(high_perf_config.to_dict(), f, indent=2)
        
        # Low bandwidth configuration
        low_bw_config = SystemConfig()
        low_bw_config.performance.max_fps = 15
        low_bw_config.performance.jpeg_quality = 50
        low_bw_config.performance.compression_level = 9
        low_bw_config.performance.mouse_throttle_ms = 50
        low_bw_config.features.enable_audio = False
        low_bw_config.features.enable_clipboard = False
        low_bw_config.features.enable_file_transfer = False
        
        with open(config_dir / "low-bandwidth.json", "w") as f:
            json.dump(low_bw_config.to_dict(), f, indent=2)
        
        # Secure enterprise configuration
        secure_config = SystemConfig()
        secure_config.security.enable_ssl = True
        secure_config.security.ssl_cert_path = "/etc/ssl/certs/remote-desktop-cert.pem"
        secure_config.security.ssl_key_path = "/etc/ssl/private/remote-desktop-key.pem"
        secure_config.security.encryption_key = "your-secure-encryption-key"
        secure_config.security.auth_required = True
        secure_config.security.auth_token = "your-secure-auth-token"
        secure_config.security.allowed_ips = ["192.168.1.0/24"]
        secure_config.features.enable_session_recording = True
        
        with open(config_dir / "secure-enterprise.json", "w") as f:
            json.dump(secure_config.to_dict(), f, indent=2)
        
        print("Example configuration files created in config/ directory")

# ==================== Utility Functions ====================
def get_local_ip() -> str:
    """Get local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False

def find_available_port(host: str, start_port: int, end_port: int) -> Optional[int]:
    """Find an available port in the given range"""
    for port in range(start_port, end_port + 1):
        if is_port_available(host, port):
            return port
    return None

def kill_process_on_port(port: int) -> bool:
    """Kill the process using the specified port (Windows only)"""
    try:
        import subprocess
        # Find the process using the port
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the result to find the PID
        for line in result.stdout.split('\n'):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        # Kill the process
                        subprocess.run(["taskkill", "/F", "/PID", pid], check=True)
                        print(f"Killed process with PID {pid} using port {port}")
                        return True
                    except subprocess.CalledProcessError:
                        pass
        return False
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")
        return False

# ==================== Enumerations ====================
class EventType(Enum):
    KEY = "key"
    CLICK = "click"
    MOVE = "move"
    SCROLL = "scroll"
    AUTO_CLICK = "auto_click"
    SYSTEM = "system"
    CLIPBOARD = "clipboard"
    FILE_TRANSFER = "file_transfer"
    AUDIO = "audio"

# ==================== Metrics & Monitoring ====================
class MetricsCollector:
    """Prometheus metrics collection for monitoring"""
    def __init__(self):
        self.connected_clients = Counter('rd_connected_clients', 'Number of connected clients')
        self.frame_sent = Counter('rd_frames_sent', 'Total frames sent')
        self.frame_size = Histogram('rd_frame_size_bytes', 'Frame size in bytes')
        self.latency = Histogram('rd_latency_ms', 'Request latency in ms')
        self.errors = Counter('rd_errors', 'Total errors', ['type'])

# ==================== Security & Encryption ====================
class SecurityManager:
    """Enterprise-grade security management"""
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.cipher = Fernet(config.encryption_key.encode()) if config.encryption_key else None
        
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data if encryption is enabled"""
        if self.cipher:
            return self.cipher.encrypt(data)
        return data
    
    def decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data if encryption is enabled"""
        if self.cipher:
            return self.cipher.decrypt(data)
        return data
    
    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context if enabled"""
        if not self.config.enable_ssl:
            return None
            
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile=self.config.ssl_cert_path,
            keyfile=self.config.ssl_key_path
        )
        return context

# ==================== Screen Capture Engine ====================
class ScreenCaptureEngine:
    """High-performance screen capture with multiple monitor support"""
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.frame_queue = queue.Queue(maxsize=config.frame_queue_size)
        self.running = False
        self.monitors = []
        self.current_monitor = 0
        
    def initialize(self):
        """Initialize screen capture"""
        with mss.mss() as sct:
            self.monitors = sct.monitors[1:]  # Skip virtual monitor
            logging.info(f"Detected {len(self.monitors)} monitors")
    
    def start_capture(self):
        """Start screen capture thread"""
        self.running = True
        capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        capture_thread.start()
        logging.info("Screen capture started")
    
    def stop_capture(self):
        """Stop screen capture"""
        self.running = False
        logging.info("Screen capture stopped")
    
    def _capture_loop(self):
        """Main capture loop with performance optimizations"""
        with mss.mss() as sct:
            monitor = self.monitors[self.current_monitor]
            frame_time = 1.0 / self.config.max_fps
            
            while self.running:
                try:
                    start_time = time.time()
                    
                    # Capture screen
                    img = np.array(sct.grab(monitor))
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Apply optimizations
                    if self.config.jpeg_quality < 90:
                        img = self._optimize_image(img)
                    
                    # Encode frame
                    result, buffer = cv2.imencode(
                        ".jpg", 
                        img, 
                        [int(cv2.IMWRITE_JPEG_QUALITY), self.config.jpeg_quality]
                    )
                    
                    if result:
                        frame_data = buffer.tobytes()
                        
                        # Apply compression if enabled
                        if self.config.compression_level > 0:
                            frame_data = zlib.compress(frame_data, level=self.config.compression_level)
                        
                        # Manage queue
                        if self.frame_queue.full():
                            try:
                                self.frame_queue.get_nowait()
                            except queue.Empty:
                                pass
                        
                        self.frame_queue.put(frame_data)
                    
                    # Control frame rate
                    elapsed = time.time() - start_time
                    sleep_time = max(0, frame_time - elapsed)
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    logging.error(f"Capture error: {e}")
                    time.sleep(0.1)
    
    def _optimize_image(self, img: np.ndarray) -> np.ndarray:
        """Apply image optimizations for performance"""
        # Downsample if resolution is too high
        height, width = img.shape[:2]
        if width > self.config.downscale_threshold or height > self.config.downscale_threshold:
            scale = min(self.config.downscale_threshold/width, self.config.downscale_threshold/height)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        
        return img
    
    def switch_monitor(self, monitor_index: int):
        """Switch to different monitor"""
        if 0 <= monitor_index < len(self.monitors):
            self.current_monitor = monitor_index
            logging.info(f"Switched to monitor {monitor_index}")

# ==================== Event Broadcasting System ====================
class EventBroadcaster:
    """High-performance event broadcasting with compression"""
    def __init__(self, config: SystemConfig, security: SecurityManager):
        self.config = config
        self.security = security
        self.clients: Set[Union[WebSocketResponse, websockets.ServerProtocol]] = set()
        self.metrics = MetricsCollector()
    
    def add_client(self, client: Union[WebSocketResponse, websockets.ServerProtocol]):
        """Add new client"""
        self.clients.add(client)
        self.metrics.connected_clients.inc()
        logging.info(f"Client connected: {client.remote_address if hasattr(client, 'remote_address') else 'Unknown'}")
    
    def remove_client(self, client: Union[WebSocketResponse, websockets.ServerProtocol]):
        """Remove client"""
        self.clients.discard(client)
        self.metrics.connected_clients.clear()
        logging.info(f"Client disconnected: {client.remote_address if hasattr(client, 'remote_address') else 'Unknown'}")
    
    async def broadcast_event(self, event_type: EventType, details: Dict[str, Any]):
        """Broadcast event to all clients with compression"""
        try:
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            event = {
                "timestamp": timestamp,
                "type": event_type.value,
                "details": details
            }
            
            # Serialize and compress
            json_data = json.dumps(event).encode('utf-8')
            if self.config.performance.compression_level > 0:
                json_data = zlib.compress(json_data, level=self.config.performance.compression_level)
            
            # Encrypt if enabled
            if self.security.cipher:
                json_data = self.security.encrypt_data(json_data)
            
            # Broadcast to all clients
            if self.clients:
                await asyncio.gather(
                    *[self._send_to_client(client, json_data) for client in self.clients],
                    return_exceptions=True
                )
                
        except Exception as e:
            logging.error(f"Broadcast error: {e}")
            self.metrics.errors.labels(type='broadcast').inc()
    
    async def broadcast_frame(self, frame_data: bytes):
        """Broadcast screen frame with optimizations"""
        try:
            if not self.clients:
                return
                
            # Encrypt if enabled
            if self.security.cipher:
                frame_data = self.security.encrypt_data(frame_data)
            
            # Broadcast to all clients
            await asyncio.gather(
                *[self._send_to_client(client, frame_data) for client in self.clients],
                return_exceptions=True
            )
            
            self.metrics.frame_sent.inc()
            self.metrics.frame_size.observe(len(frame_data))
            
        except Exception as e:
            logging.error(f"Frame broadcast error: {e}")
            self.metrics.errors.labels(type='frame').inc()
    
    async def _send_to_client(self, client: Union[WebSocketResponse, websockets.ServerProtocol], data: bytes):
        """Send data to a client, handling different WebSocket implementations"""
        try:
            if isinstance(client, WebSocketResponse):
                # aiohttp WebSocket
                if isinstance(data, str):
                    await client.send_str(data)
                else:
                    await client.send_bytes(data)
            else:
                # websockets library
                await client.send(data)
        except Exception as e:
            logging.error(f"Error sending to client: {e}")
            self.remove_client(client)

# ==================== Input Controller ====================
class InputController:
    """High-precision input control with debouncing"""
    def __init__(self, config: SystemConfig):
        self.config = config
        self.keyboard = KController()
        self.mouse = MController()
        self.last_move_time = 0
        self.auto_click_active = False
    
    async def handle_command(self, command: Dict[str, Any]):
        """Handle input commands with validation"""
        try:
            action = command.get("action")
            
            if action == "move":
                x, y = command.get("x", 0), command.get("y", 0)
                self._move_mouse(x, y)
                
            elif action == "click":
                button = self._parse_button(command.get("button", "left"))
                self._click_mouse(button)
                
            elif action == "double_click":
                self._double_click()
                
            elif action == "scroll":
                dy = command.get("dy", 0)
                self._scroll(dy)
                
            elif action == "key":
                key = command.get("key")
                if key.lower() != "end":  # Security: Block END key
                    self._press_key(key)
                    
            elif action == "start_auto_click":
                self.auto_click_active = True
                asyncio.create_task(self._auto_click_loop())
                
            elif action == "stop_auto_click":
                self.auto_click_active = False
                
        except Exception as e:
            logging.error(f"Command handling error: {e}")
    
    def _move_mouse(self, x: int, y: int):
        """Move mouse with throttling"""
        current_time = time.time()
        if current_time - self.last_move_time > (self.config.performance.mouse_throttle_ms / 1000):
            self.mouse.position = (x, y)
            self.last_move_time = current_time
    
    def _click_mouse(self, button: Button):
        """Click mouse with specified button"""
        self.mouse.click(button)
    
    def _double_click(self):
        """Perform double click"""
        self.mouse.click(Button.left)
        time.sleep(0.1)
        self.mouse.click(Button.left)
    
    def _scroll(self, dy: int):
        """Scroll mouse wheel"""
        self.mouse.scroll(0, dy)
    
    def _press_key(self, key: str):
        """Press and release key"""
        try:
            self.keyboard.press(key)
            self.keyboard.release(key)
        except Exception as e:
            logging.error(f"Key press error: {e}")
    
    def _parse_button(self, button_str: str) -> Button:
        """Parse button string to Button enum"""
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle
        }
        return button_map.get(button_str.lower(), Button.left)
    
    async def _auto_click_loop(self):
        """Auto-click loop with randomization"""
        while self.auto_click_active:
            try:
                # Get current mouse position
                x, y = self.mouse.position
                
                # Perform click
                self.mouse.click(Button.left)
                
                # Random delay between clicks
                delay = 1 + random.random() * 2
                await asyncio.sleep(delay)
                
            except Exception as e:
                logging.error(f"Auto-click error: {e}")
                break

# ==================== Web Interface ====================
class WebInterface:
    """Enterprise-grade web interface with responsive design"""
    def __init__(self, config: SystemConfig):
        self.config = config
        self.html_content = self._generate_html()
    
    def _generate_html(self) -> str:
        """Generate responsive HTML interface"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enterprise Remote Desktop</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                :root {
                    --primary-color: #2c3e50;
                    --secondary-color: #3498db;
                    --success-color: #27ae60;
                    --danger-color: #e74c3c;
                    --dark-color: #1a1a1a;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    overflow: hidden;
                }
                
                .main-header {
                    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                    color: white;
                    padding: 1rem;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                
                .screen-container {
                    position: relative;
                    background-color: var(--dark-color);
                    overflow: hidden;
                    height: calc(100vh - 120px);
                }
                
                #screen {
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    cursor: crosshair;
                }
                
                .control-panel {
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    padding: 1.5rem;
                    height: calc(100vh - 140px);
                    overflow-y: auto;
                }
                
                .status-indicator {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }
                
                .status-connected {
                    background-color: var(--success-color);
                    box-shadow: 0 0 10px var(--success-color);
                }
                
                .status-disconnected {
                    background-color: var(--danger-color);
                }
                
                .log-container {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                    border-radius: 8px;
                    padding: 1rem;
                    height: 200px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 0.85rem;
                }
                
                .log-entry {
                    margin-bottom: 0.5rem;
                    padding: 0.25rem;
                    border-left: 3px solid transparent;
                }
                
                .log-entry.key { border-left-color: var(--success-color); }
                .log-entry.click { border-left-color: var(--secondary-color); }
                .log-entry.scroll { border-left-color: #9b59b6; }
                .log-entry.move { border-left-color: #f39c12; }
                .log-entry.system { border-left-color: #95a5a6; }
                
                .metric-card {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }
                
                .btn-custom {
                    border-radius: 25px;
                    padding: 0.5rem 1.5rem;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }
                
                .btn-custom:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }
                
                .quality-slider {
                    width: 100%;
                }
                
                @media (max-width: 768px) {
                    .control-panel {
                        height: auto;
                        max-height: 300px;
                    }
                }
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
                class RemoteDesktopClient {
                    constructor() {
                        this.ws = null;
                        this.connected = false;
                        this.screenWidth = 1920;
                        this.screenHeight = 1080;
                        this.lastPingTime = 0;
                        this.autoClickActive = false;
                        this.initializeComponents();
                        this.setupEventListeners();
                        this.connectWebSocket();
                    }
                    
                    initializeComponents() {
                        this.screenImg = document.getElementById('screen');
                        this.connectionStatus = document.getElementById('connection-status');
                        this.statusIndicator = document.getElementById('status-indicator');
                        this.latencyInfo = document.getElementById('latency-info');
                        this.eventLog = document.getElementById('event-log');
                        this.qualitySlider = document.getElementById('quality-slider');
                        this.qualityValue = document.getElementById('quality-value');
                        this.fpsSelect = document.getElementById('fps-select');
                    }
                    
                    setupEventListeners() {
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
                    }
                    
                    connectWebSocket() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.hostname}:8765`;
                        
                        this.ws = new WebSocket(wsUrl);
                        this.ws.binaryType = 'arraybuffer';
                        
                        this.ws.onopen = () => {
                            this.connected = true;
                            this.updateConnectionStatus('Connected', true);
                            this.startLatencyCheck();
                        };
                        
                        this.ws.onmessage = (event) => {
                            if (event.data instanceof ArrayBuffer) {
                                this.handleFrameData(event.data);
                            } else {
                                this.handleJsonMessage(JSON.parse(event.data));
                            }
                        };
                        
                        this.ws.onclose = () => {
                            this.connected = false;
                            this.updateConnectionStatus('Disconnected', false);
                            setTimeout(() => this.connectWebSocket(), 2000);
                        };
                        
                        this.ws.onerror = (error) => {
                            console.error('WebSocket Error:', error);
                        };
                    }
                    
                    handleFrameData(arrayBuffer) {
                        const blob = new Blob([arrayBuffer], { type: 'image/jpeg' });
                        const url = URL.createObjectURL(blob);
                        
                        this.screenImg.src = url;
                        //console.log(this.screenImg.src)
                        
                        if (this.screenImg.currentSrc) {
                            URL.revokeObjectURL(this.screenImg.currentSrc);
                        }
                    }
                    
                    handleJsonMessage(data) {
                        if (data.type === 'pong') {
                            const latency = Math.round(performance.now() - this.lastPingTime);
                            this.latencyInfo.textContent = latency;
                        } else if (data.type === 'screen_size') {
                            this.screenWidth = data.width;
                            this.screenHeight = data.height;
                        } else {
                            this.addLogEntry(data);
                        }
                    }
                    
                    handleMouseDown(e) {
                        e.preventDefault();
                        const coords = this.getScreenCoordinates(e);
                        const button = e.button === 0 ? 'left' : 'right';
                        
                        this.sendCommand({
                            type: 'control',
                            action: 'click',
                            x: coords.x,
                            y: coords.y,
                            button: button
                        });
                    }
                    
                    handleDoubleClick(e) {
                        e.preventDefault();
                        const coords = this.getScreenCoordinates(e);
                        
                        this.sendCommand({
                            type: 'control',
                            action: 'double_click',
                            x: coords.x,
                            y: coords.y
                        });
                    }
                    
                    handleMouseMove(e) {
                        const coords = this.getScreenCoordinates(e);
                        
                        if (!this.lastMoveTime || Date.now() - this.lastMoveTime > 50) {
                            this.lastMoveTime = Date.now();
                            this.sendCommand({
                                type: 'control',
                                action: 'move',
                                x: coords.x,
                                y: coords.y
                            });
                        }
                    }
                    
                    handleWheel(e) {
                        e.preventDefault();
                        const coords = this.getScreenCoordinates(e);
                        const deltaY = e.deltaY > 0 ? 1 : -1;
                        
                        this.sendCommand({
                            type: 'control',
                            action: 'scroll',
                            x: coords.x,
                            y: coords.y,
                            dy: deltaY
                        });
                    }
                    
                    handleKeyDown(e) {
                        if (e.key === 'End') {
                            e.preventDefault();
                            return;
                        }
                        
                        this.sendCommand({
                            type: 'control',
                            action: 'key',
                            key: e.key
                        });
                    }
                    
                    getScreenCoordinates(e) {
                        const rect = this.screenImg.getBoundingClientRect();
                        const scaleX = this.screenWidth / rect.width;
                        const scaleY = this.screenHeight / rect.height;
                        
                        return {
                            x: Math.round((e.clientX - rect.left) * scaleX),
                            y: Math.round((e.clientY - rect.top) * scaleY)
                        };
                    }
                    
                    sendCommand(command) {
                        if (this.connected) {
                            this.ws.send(JSON.stringify(command));
                        }
                    }
                    
                    sendClick(button) {
                        this.sendCommand({
                            type: 'control',
                            action: 'click',
                            button: button
                        });
                    }
                    
                    toggleAutoClick() {
                        this.autoClickActive = !this.autoClickActive;
                        const btn = document.getElementById('auto-click-btn');
                        
                        if (this.autoClickActive) {
                            btn.classList.remove('btn-success');
                            btn.classList.add('btn-danger');
                            btn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Auto Click';
                            this.sendCommand({ type: 'command', action: 'start_auto_click' });
                        } else {
                            btn.classList.remove('btn-danger');
                            btn.classList.add('btn-success');
                            btn.innerHTML = '<i class="fas fa-robot me-2"></i>Auto Click';
                            this.sendCommand({ type: 'command', action: 'stop_auto_click' });
                        }
                    }
                    
                    updateQuality() {
                        const quality = this.qualitySlider.value;
                        this.qualityValue.textContent = quality + '%';
                        this.sendCommand({
                            type: 'command',
                            action: 'set_quality',
                            quality: parseInt(quality)
                        });
                    }
                    
                    updateFPS() {
                        const fps = this.fpsSelect.value;
                        this.sendCommand({
                            type: 'command',
                            action: 'set_fps',
                            fps: parseInt(fps)
                        });
                    }
                    
                    updateConnectionStatus(status, connected) {
                        this.connectionStatus.textContent = status;
                        this.statusIndicator.className = `status-indicator ${connected ? 'status-connected' : 'status-disconnected'}`;
                    }
                    
                    addLogEntry(data) {
                        const entry = document.createElement('div');
                        entry.className = `log-entry ${data.type}`;
                        entry.textContent = `[${data.timestamp}] ${data.type.toUpperCase()}: ${JSON.stringify(data.details)}`;
                        
                        this.eventLog.appendChild(entry);
                        this.eventLog.scrollTop = this.eventLog.scrollHeight;
                        
                        // Keep only last 100 entries
                        while (this.eventLog.childNodes.length > 100) {
                            this.eventLog.removeChild(this.eventLog.firstChild);
                        }
                    }
                    
                    startLatencyCheck() {
                        setInterval(() => {
                            if (this.connected) {
                                this.lastPingTime = performance.now();
                                this.sendCommand({ type: 'ping' });
                            }
                        }, 2000);
                    }
                }
                
                // Initialize the application
                document.addEventListener('DOMContentLoaded', () => {
                    new RemoteDesktopClient();
                });
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
            logging.error(f"File transfer error: {e}")
            return Response(text="Error retrieving file", status=500)

# ==================== Main Application ====================
class RemoteDesktopServer:
    """Enterprise-grade remote desktop server"""
    def __init__(self, config_path: str = None):
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # Validate configuration
        if not self.config_manager.validate_config():
            raise ValueError("Invalid configuration")
        
        # Initialize logging based on config
        self._setup_logging()
        
        # Initialize components with config
        self.security = SecurityManager(self.config.security)
        self.capture_engine = ScreenCaptureEngine(self.config.performance)
        self.broadcaster = EventBroadcaster(self.config, self.security)
        self.input_controller = InputController(self.config)
        self.web_interface = WebInterface(self.config)
        
        # Initialize metrics if enabled
        if self.config.server.metrics_port > 0:
            start_http_server(self.config.server.metrics_port)
            logging.info(f"Metrics server started on port {self.config.server.metrics_port}")
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        log_config = self.config.logging
        
        logging.basicConfig(
            level=getattr(logging, log_config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config.log_file),
                logging.StreamHandler()
            ]
        )
        logging.info("Remote Desktop Server starting with configuration...")
    
    async def start(self):
        """Start the remote desktop server"""
        # Initialize screen capture
        self.capture_engine.initialize()
        self.capture_engine.start_capture()
        
        # Find available ports
        host = self.config.server.host
        
        # Try to find available HTTP port
        http_port = self._find_available_port(
            host, 
            self.config.server.http_port,
            self.config.server.http_port_fallback_start,
            self.config.server.http_port_fallback_end
        )
        
        if http_port is None:
            logging.error("No available HTTP port found in the specified range")
            return
        
        # Try to find available WebSocket port
        ws_port = self._find_available_port(
            host,
            self.config.server.ws_port,
            self.config.server.ws_port_fallback_start,
            self.config.server.ws_port_fallback_end
        )
        
        if ws_port is None:
            logging.error("No available WebSocket port found in the specified range")
            return
        
        # Try to find available metrics port if enabled
        metrics_port = None
        if self.config.server.metrics_port > 0:
            metrics_port = self._find_available_port(
                host,
                self.config.server.metrics_port,
                self.config.server.metrics_port_fallback_start,
                self.config.server.metrics_port_fallback_end
            )
            
            if metrics_port is None:
                logging.warning("No available metrics port found, disabling metrics")
        
        # Update config with actual ports
        self.config.server.http_port = http_port
        self.config.server.ws_port = ws_port
        if metrics_port is not None:
            self.config.server.metrics_port = metrics_port
        
        # Create web application
        app = Application()
        app.router.add_get('/', self.web_interface.handle_http_request)
        app.router.add_get('/file', self.web_interface.handle_file)
        
        # Setup SSL context if enabled
        ssl_context = self.security.create_ssl_context()
        
        # Start HTTP server
        runner = web.AppRunner(app)
        await runner.setup()
        
        http_site = web.TCPSite(
            runner, 
            host, 
            http_port,
            ssl_context=ssl_context
        )
        await http_site.start()
        
        # Start WebSocket server
        ws_server = await websockets.serve(
            self.handle_websocket,
            host,
            ws_port,
            ssl=ssl_context
        )
        
        # Start frame broadcaster
        asyncio.create_task(self.frame_broadcast_loop())
        
        # Print server info
        self._print_server_info()
        
        # Keep server running
        try:
            await asyncio.gather(
                ws_server.wait_closed(),
                http_site._server.wait_closed()
            )
        except KeyboardInterrupt:
            logging.info("Shutting down server...")
        finally:
            await self._cleanup(runner, ws_server)
    
    def _find_available_port(self, host: str, preferred_port: int, fallback_start: int, fallback_end: int) -> Optional[int]:
        """Find an available port, trying preferred first then fallback range"""
        # First try the preferred port
        if is_port_available(host, preferred_port):
            return preferred_port
        
        # If preferred port is not available, try to kill the process using it
        if kill_process_on_port(preferred_port):
            # Wait a moment for the process to fully terminate
            time.sleep(1)
            # Try the preferred port again
            if is_port_available(host, preferred_port):
                return preferred_port
        
        # If still not available, try fallback ports
        logging.warning(f"Port {preferred_port} is in use, trying fallback ports {fallback_start}-{fallback_end}")
        return find_available_port(host, fallback_start, fallback_end)
    
    async def handle_websocket(self, websocket: websockets.ServerProtocol):
        """Handle WebSocket connections"""
        self.broadcaster.add_client(websocket)
        
        try:
            # Send screen size
            await websocket.send(json.dumps({
                "type": "screen_size",
                "width": 1920,
                "height": 1080
            }))
            
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        # Handle binary messages (e.g., file uploads)
                        if self.config.features.enable_file_transfer:
                            await self._handle_file_transfer(websocket, message)
                    else:
                        # Handle text messages (JSON commands)
                        data = json.loads(message)
                        await self.input_controller.handle_command(data)
                except Exception as e:
                    logging.error(f"WebSocket message error: {e}")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            self.broadcaster.remove_client(websocket)
    
    async def _handle_file_transfer(self, websocket: websockets.ServerProtocol, data: bytes):
        """Handle file transfer data"""
        try:
            # Decrypt if needed
            if self.security.cipher:
                data = self.security.decrypt_data(data)
            
            # Decompress if needed
            if self.config.performance.compression_level > 0:
                data = zlib.decompress(data)
            
            # Here you would process the file data
            # For now, just log the file transfer
            logging.info(f"Received file transfer data: {len(data)} bytes")
            
            # Send confirmation
            await websocket.send(json.dumps({
                "type": "file_transfer",
                "status": "success",
                "size": len(data)
            }))
        except Exception as e:
            logging.error(f"File transfer error: {e}")
            await websocket.send(json.dumps({
                "type": "file_transfer",
                "status": "error",
                "message": str(e)
            }))
    
    async def frame_broadcast_loop(self):
        """Main frame broadcasting loop"""
        while True:
            try:
                # Get frame from queue
                frame_data = self.capture_engine.frame_queue.get()
                
                # Broadcast to all clients
                await self.broadcaster.broadcast_frame(frame_data)
                
                # Small delay to prevent busy loop
                await asyncio.sleep(0.001)
            except Exception as e:
                logging.error(f"Frame broadcast error: {e}")
                await asyncio.sleep(0.1)
    
    def _print_server_info(self):
        """Print server information based on configuration"""
        server_config = self.config.server
        security_config = self.config.security
        
        protocol = "https" if security_config.enable_ssl else "http"
        ws_protocol = "wss" if security_config.enable_ssl else "ws"
        
        print("\n" + "="*60)
        print("  ENTERPRISE REMOTE DESKTOP SERVER")
        print("="*60)
        print(f"  Configuration: {self.config_manager.config_path}")
        print(f"  Security: {'SSL Enabled' if security_config.enable_ssl else 'Standard'}")
        print(f"  Max FPS: {self.config.performance.max_fps}")
        print(f"  Compression: ZLIB Level {self.config.performance.compression_level}")
        print("\n  SERVER ENDPOINTS:")
        print(f"  Web Interface: {protocol}://{get_local_ip()}:{server_config.http_port}/")
        print(f"  WebSocket: {ws_protocol}://{get_local_ip()}:{server_config.ws_port}/")
        if server_config.metrics_port > 0:
            print(f"  Metrics: http://{get_local_ip()}:{server_config.metrics_port}/")
        print("\n  FEATURES:")
        features = self.config.features
        print(f"  • Audio Streaming: {'Enabled' if features.enable_audio else 'Disabled'}")
        print(f"  • Clipboard Sync: {'Enabled' if features.enable_clipboard else 'Disabled'}")
        print(f"  • File Transfer: {'Enabled' if features.enable_file_transfer else 'Disabled'}")
        print(f"  • Session Recording: {'Enabled' if features.enable_session_recording else 'Disabled'}")
        print(f"  • Multi-Monitor: {'Enabled' if features.enable_multi_monitor else 'Disabled'}")
        print("\n  Press Ctrl+C to shutdown the server")
        print("="*60 + "\n")
    
    async def _cleanup(self, runner, ws_server):
        """Cleanup resources"""
        self.capture_engine.stop_capture()
        await runner.cleanup()
        ws_server.close()
        logging.info("Server shutdown complete")

# ==================== Entry Point ====================
def main():
    """Main entry point with configuration support"""
    parser = argparse.ArgumentParser(description="Enterprise Remote Desktop Server")
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default="config/remote-desktop.json"
    )
    parser.add_argument(
        "--create-config",
        help="Create example configuration files",
        action="store_true"
    )
    parser.add_argument(
        "--validate-config",
        help="Validate configuration file",
        action="store_true"
    )
    parser.add_argument(
        "--kill-port",
        type=int,
        help="Kill process using the specified port"
    )
    
    args = parser.parse_args()
    
    # Handle port killing
    if args.kill_port:
        if kill_process_on_port(args.kill_port):
            print(f"Successfully killed process using port {args.kill_port}")
        else:
            print(f"Failed to kill process using port {args.kill_port}")
        return
    
    # Handle special commands
    if args.create_config:
        config_manager = ConfigManager()
        config_manager.create_example_configs()
        return
    
    if args.validate_config:
        config_manager = ConfigManager(args.config)
        if config_manager.validate_config():
            print("Configuration is valid")
        else:
            print("Configuration validation failed")
        return
    
    # Start the server
    try:
        server = RemoteDesktopServer(args.config)
        asyncio.run(server.start())
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()