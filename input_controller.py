import time
import pyautogui
from typing import Tuple, Optional

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class InputController:
    def __init__(self) -> None:
        pass

    def press_key(self, key: str, duration: float = 0.1) -> None:
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)

    def click_position(self, x: int, y: int, clicks: int = 1, button: str = "left") -> None:
        pyautogui.click(x=x, y=y, clicks=clicks, button=button)

    def move_to(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)

    def hold_key(self, key: str) -> None:
        pyautogui.keyDown(key)

    def release_key(self, key: str) -> None:
        pyautogui.keyUp(key)