# Enterprise Remote Desktop System

This is a comprehensive remote desktop application built with Python that allows remote control of a computer through a web interface.

## Features
- Real-time screen sharing
- Remote mouse and keyboard control
- Multi-monitor support
- Security features (SSL, encryption)
- Performance optimizations
- Configuration management
- Metrics collection

## Architecture
The application has been refactored into several modules:
- `config.py`: Configuration management
- `capture.py`: Screen capture functionality
- `controller.py`: Input control
- `security.py`: Security and encryption
- `web.py`: Web interface and server
- `server.py`: Main server orchestration
- `utils.py`: Utility functions
- `models.py`: Data models and enums

## Requirements
- Python 3.8+
- OpenCV
- mss
- pynput
- websockets
- aiohttp
- cryptography
- prometheus_client
- numpy

## Installation
```bash
pip install opencv-python mss pynput websockets aiohttp cryptography prometheus_client numpy
```

## Usage
```bash
python server.py --config config/remote-desktop.json
```

## License
Enterprise License