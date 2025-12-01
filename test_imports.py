#!/usr/bin/env python3
"""
Test script to verify all modules can be imported correctly
"""
import sys

def test_imports():
    print("Testing imports...")
    
    try:
        from models import SystemConfig, EventType
        print("✓ models imported successfully")
    except ImportError as e:
        print(f"✗ models import failed: {e}")
        return False
    
    try:
        from utils import get_local_ip, is_port_available
        print("✓ utils imported successfully")
    except ImportError as e:
        print(f"✗ utils import failed: {e}")
        return False
    
    try:
        from config import ConfigManager
        print("✓ config imported successfully")
    except ImportError as e:
        print(f"✗ config import failed: {e}")
        return False
    
    try:
        from security import SecurityManager, MetricsCollector
        print("✓ security imported successfully")
    except ImportError as e:
        print(f"✗ security import failed: {e}")
        return False
    
    try:
        from capture import ScreenCaptureEngine, EventBroadcaster
        print("✓ capture imported successfully")
    except ImportError as e:
        print(f"✗ capture import failed: {e}")
        return False
    
    try:
        from controller import InputController
        print("✓ controller imported successfully")
    except ImportError as e:
        # On headless systems, pynput may not work but the module should still import
        if "failed to acquire X connection" in str(e) or "display" in str(e).lower():
            print("⚠ controller import warning: pynput may not work in headless environment (this is expected)")
        else:
            print(f"✗ controller import failed: {e}")
            return False
    except Exception as e:
        # On headless systems, pynput may fail on import due to X11 issues
        if "failed to acquire X connection" in str(e) or "display" in str(e).lower():
            print("⚠ controller import warning: pynput may not work in headless environment (this is expected)")
        else:
            print(f"✗ controller import failed: {e}")
            return False
    
    try:
        from web import WebInterface
        print("✓ web imported successfully")
    except ImportError as e:
        print(f"✗ web import failed: {e}")
        return False
    
    try:
        from server import RemoteDesktopServer
        print("✓ server imported successfully")
    except ImportError as e:
        # On headless systems, pynput may not work but the module should still import
        if "failed to acquire X connection" in str(e) or "display" in str(e).lower():
            print("⚠ server import warning: pynput may not work in headless environment (this is expected)")
        else:
            print(f"✗ server import failed: {e}")
            return False
    except Exception as e:
        # On headless systems, pynput may fail on import due to X11 issues
        if "failed to acquire X connection" in str(e) or "display" in str(e).lower():
            print("⚠ server import warning: pynput may not work in headless environment (this is expected)")
        else:
            print(f"✗ server import failed: {e}")
            return False
    
    print("\nAll imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    if not success:
        sys.exit(1)