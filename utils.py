"""
Utility functions for the remote desktop system
"""
import socket
import os
from typing import Optional


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