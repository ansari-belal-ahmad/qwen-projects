"""
Security and encryption for the remote desktop system
"""
import ssl
from typing import Optional
from cryptography.fernet import Fernet
from models import SecurityConfig
from prometheus_client import Counter, Histogram


class MetricsCollector:
    """Prometheus metrics collection for monitoring"""
    def __init__(self):
        self.connected_clients = Counter('rd_connected_clients', 'Number of connected clients')
        self.frame_sent = Counter('rd_frames_sent', 'Total frames sent')
        self.frame_size = Histogram('rd_frame_size_bytes', 'Frame size in bytes')
        self.latency = Histogram('rd_latency_ms', 'Request latency in ms')
        self.errors = Counter('rd_errors', 'Total errors', ['type'])


class SecurityManager:
    """Enterprise-grade security management"""
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.cipher = None
        if config.encryption_key:
            try:
                self.cipher = Fernet(config.encryption_key.encode())
            except Exception as e:
                print(f"Error initializing encryption: {e}")
                self.cipher = None

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