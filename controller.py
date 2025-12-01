"""
Input control for the remote desktop system
"""
import asyncio
import time
import logging
import random
from pynput import keyboard, mouse
from pynput.keyboard import Controller as KController, Key
from pynput.mouse import Controller as MController, Button
from models import SystemConfig


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