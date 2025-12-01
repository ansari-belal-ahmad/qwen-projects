"""
Screen capture functionality for the remote desktop system
"""
import asyncio
import threading
import queue
import time
import zlib
import logging
import cv2
import mss
import numpy as np
from typing import Set, Union
from aiohttp.web import WebSocketResponse
import websockets
from websockets.server import ServerProtocol
from models import PerformanceConfig, EventType
from security import SecurityManager, MetricsCollector


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


class EventBroadcaster:
    """High-performance event broadcasting with compression"""
    def __init__(self, config, security: SecurityManager):
        self.config = config
        self.security = security
        self.clients: Set[Union[WebSocketResponse, ServerProtocol]] = set()
        self.metrics = MetricsCollector()

    def add_client(self, client: Union[WebSocketResponse, ServerProtocol]):
        """Add new client"""
        self.clients.add(client)
        self.metrics.connected_clients.inc()
        logging.info(f"Client connected: {client.remote_address if hasattr(client, 'remote_address') else 'Unknown'}")

    def remove_client(self, client: Union[WebSocketResponse, ServerProtocol]):
        """Remove client"""
        self.clients.discard(client)
        self.metrics.connected_clients.clear()
        logging.info(f"Client disconnected: {client.remote_address if hasattr(client, 'remote_address') else 'Unknown'}")

    async def broadcast_event(self, event_type: EventType, details: dict):
        """Broadcast event to all clients with compression"""
        try:
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            event = {
                "timestamp": timestamp,
                "type": event_type.value,
                "details": details
            }

            # Serialize and compress
            json_data = str(event).encode('utf-8')
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

    async def _send_to_client(self, client: Union[WebSocketResponse, ServerProtocol], data: bytes):
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