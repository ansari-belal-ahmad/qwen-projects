"""
Input control for the remote desktop system
"""
import asyncio
import time
import logging
import random
from models import SystemConfig

# Handle pynput import gracefully for headless environments
try:
    from pynput import keyboard, mouse
    from pynput.keyboard import Controller as KController, Key
    from pynput.mouse import Controller as MController, Button
    PYNPUT_AVAILABLE = True
except ImportError as e:
    # Create mock objects for headless environments
    class MockController:
        def __init__(self):
            pass
        def press(self, *args, **kwargs):
            pass
        def release(self, *args, **kwargs):
            pass
        def click(self, *args, **kwargs):
            pass
        def scroll(self, *args, **kwargs):
            pass
        @property
        def position(self):
            return (0, 0)
        @position.setter
        def position(self, value):
            pass

    class MockKey:
        space = 'space'
        enter = 'enter'
        tab = 'tab'
        backspace = 'backspace'
        delete = 'delete'
        esc = 'esc'
        shift = 'shift'
        ctrl = 'ctrl'
        alt = 'alt'
        cmd = 'cmd'
        caps_lock = 'caps_lock'
        num_lock = 'num_lock'
        scroll_lock = 'scroll_lock'
        pause = 'pause'
        insert = 'insert'
        home = 'home'
        end = 'end'
        page_up = 'page_up'
        page_down = 'page_down'
        left = 'left'
        right = 'right'
        up = 'up'
        down = 'down'
        f1 = 'f1'
        f2 = 'f2'
        f3 = 'f3'
        f4 = 'f4'
        f5 = 'f5'
        f6 = 'f6'
        f7 = 'f7'
        f8 = 'f8'
        f9 = 'f9'
        f10 = 'f10'
        f11 = 'f11'
        f12 = 'f12'

    class MockButton:
        left = 'left'
        right = 'right'
        middle = 'middle'

    keyboard = mouse = None
    KController = MockController
    Key = MockKey
    MController = MockController
    Button = MockButton
    PYNPUT_AVAILABLE = False


class InputController:
    """High-precision input control with debouncing"""
    def __init__(self, config: SystemConfig):
        self.config = config
        self.keyboard = KController()
        self.mouse = MController()
        self.last_move_time = 0
        self.auto_click_active = False

    async def handle_command(self, command: dict):
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
                if key and (key.lower() != "end" or not self.config.security.block_end_key):  # Security: Block END key (case-insensitive) based on config
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
            # Handle special keys by converting them to the appropriate Key object
            if isinstance(key, str):
                # Map special keys to their Key objects
                special_keys = {
                    'space': Key.space,
                    'enter': Key.enter,
                    'tab': Key.tab,
                    'backspace': Key.backspace,
                    'delete': Key.delete,
                    'escape': Key.esc,
                    'esc': Key.esc,
                    'shift': Key.shift,
                    'ctrl': Key.ctrl,
                    'alt': Key.alt,
                    'cmd': Key.cmd,
                    'win': Key.cmd,
                    'caps_lock': Key.caps_lock,
                    'num_lock': Key.num_lock,
                    'scroll_lock': Key.scroll_lock,
                    'pause': Key.pause,
                    'insert': Key.insert,
                    'home': Key.home,
                    'end': Key.end,
                    'page_up': Key.page_up,
                    'page_down': Key.page_down,
                    'left': Key.left,
                    'right': Key.right,
                    'up': Key.up,
                    'down': Key.down,
                    'f1': Key.f1,
                    'f2': Key.f2,
                    'f3': Key.f3,
                    'f4': Key.f4,
                    'f5': Key.f5,
                    'f6': Key.f6,
                    'f7': Key.f7,
                    'f8': Key.f8,
                    'f9': Key.f9,
                    'f10': Key.f10,
                    'f11': Key.f11,
                    'f12': Key.f12,
                }
                
                # If the key is a special key, use the Key object
                if key.lower() in special_keys:
                    key_obj = special_keys[key.lower()]
                    self.keyboard.press(key_obj)
                    self.keyboard.release(key_obj)
                else:
                    # For regular characters, just type them
                    self.keyboard.press(key)
                    self.keyboard.release(key)
            else:
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