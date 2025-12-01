"""
Main server for the remote desktop system
"""
import asyncio
import json
import time
import logging
import sys
import os
import argparse
import zlib
from pathlib import Path
from typing import Optional
from aiohttp import web
from aiohttp.web import Application
import websockets
from websockets.server import ServerProtocol
from models import SystemConfig
from config import ConfigManager
from capture import ScreenCaptureEngine, EventBroadcaster
from controller import InputController
from security import SecurityManager
from web import WebInterface
from utils import get_local_ip, is_port_available, find_available_port, kill_process_on_port
from prometheus_client import start_http_server


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

    async def handle_websocket(self, websocket: ServerProtocol):
        """Handle WebSocket connections"""
        self.broadcaster.add_client(websocket)

        try:
            # Get actual screen dimensions from capture engine
            screen_width = 1920
            screen_height = 1080
            
            # If capture engine is initialized, get actual dimensions from the first monitor
            if hasattr(self.capture_engine, 'monitors') and self.capture_engine.monitors:
                try:
                    first_monitor = self.capture_engine.monitors[0]
                    screen_width = first_monitor.get('width', 1920) if isinstance(first_monitor, dict) else 1920
                    screen_height = first_monitor.get('height', 1080) if isinstance(first_monitor, dict) else 1080
                except (IndexError, AttributeError, KeyError):
                    # Fallback to defaults if there's an issue accessing monitor dimensions
                    screen_width = 1920
                    screen_height = 1080

            # Send screen size
            await websocket.send(json.dumps({
                "type": "screen_size",
                "width": screen_width,
                "height": screen_height
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
                        
                        # Handle different command types
                        cmd_type = data.get('type', 'control')
                        
                        if cmd_type == 'control':
                            # These are input control commands (mouse, keyboard, etc.)
                            await self.input_controller.handle_command(data)
                        elif cmd_type == 'command':
                            # These are system commands (auto-click, settings, etc.)
                            await self._handle_system_command(data)
                        elif cmd_type == 'ping':
                            # Respond to ping for latency measurement
                            await websocket.send(json.dumps({"type": "pong"}))
                        else:
                            # Unknown command type
                            logging.warning(f"Unknown command type: {cmd_type}")
                except Exception as e:
                    logging.error(f"WebSocket message error: {e}")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            self.broadcaster.remove_client(websocket)

    async def _handle_file_transfer(self, websocket: ServerProtocol, data: bytes):
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

    async def _handle_system_command(self, data: dict):
        """Handle system commands from the client"""
        try:
            action = data.get('action')
            
            if action == 'start_auto_click':
                # Trigger start auto click in the input controller
                await self.input_controller.handle_command({'action': 'start_auto_click'})
            elif action == 'stop_auto_click':
                # Trigger stop auto click in the input controller
                await self.input_controller.handle_command({'action': 'stop_auto_click'})
            elif action == 'set_quality':
                # Handle quality setting (would update performance config in a full implementation)
                quality = data.get('quality', 75)
                logging.info(f"Quality setting changed to: {quality}%")
            elif action == 'set_fps':
                # Handle FPS setting (would update performance config in a full implementation)
                fps = data.get('fps', 30)
                logging.info(f"FPS setting changed to: {fps}")
            else:
                logging.warning(f"Unknown system command action: {action}")
        except Exception as e:
            logging.error(f"System command handling error: {e}")

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