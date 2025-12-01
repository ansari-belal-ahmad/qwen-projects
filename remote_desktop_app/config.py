"""
Configuration management for the remote desktop system
"""
import json
import os
from pathlib import Path
from typing import Optional
from models import SystemConfig


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