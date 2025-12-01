"""
Data models and enumerations for the remote desktop system
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


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
    ssl_cert_path: str = None
    ssl_key_path: str = None
    encryption_key: str = None
    auth_required: bool = False
    auth_token: str = None
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


class EventType(Enum):
    """Event types for the system"""
    KEY = "key"
    CLICK = "click"
    MOVE = "move"
    SCROLL = "scroll"
    AUTO_CLICK = "auto_click"
    SYSTEM = "system"
    CLIPBOARD = "clipboard"
    FILE_TRANSFER = "file_transfer"
    AUDIO = "audio"