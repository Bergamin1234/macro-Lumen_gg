import ctypes
import time
import pyautogui

pyautogui.FAILSAFE = True


class InputController:
    def __init__(self) -> None:
        pass

    def press_key(self, key: str, duration: float = 0.1) -> None:
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)

    def click_position(self, x: int, y: int, clicks: int = 1, button: str = "left") -> None:
        """Realiza um clique físico no ponteiro do Windows direto na coordenada da tela."""
        for _ in range(clicks):
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
            time.sleep(0.05)
            # Send Mouse Left Down (0x0002) and Left Up (0x0004)
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(0.1)

    def hold_key(self, key: str) -> None:
        pyautogui.keyDown(key)

    def release_key(self, key: str) -> None:
        pyautogui.keyUp(key)