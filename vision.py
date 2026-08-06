import logging
import os
import time
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from config import Config
from input_controller import InputController
from mss import mss
from PIL import Image


class VisionSystem:
    def __init__(self, config: Config, input_ctrl: InputController) -> None:
        self.config = config
        self.input_ctrl = input_ctrl
        self.logger = logging.getLogger("LumenaMacro.Vision")
        self.sct = mss()
        self.templates: Dict[str, np.ndarray] = {}
        self.load_templates()

    def load_templates(self) -> None:
        path = self.config.templates_path
        if not os.path.exists(path):
            os.makedirs(path)
            self.logger.warning(f"Diretório '{path}' criado. Adicione os templates em PNG.")
            return

        for filename in os.listdir(path):
            if filename.endswith(".png"):
                name = os.path.splitext(filename)[0]
                full_path = os.path.join(path, filename)
                template = cv2.imread(full_path, cv2.IMREAD_COLOR)
                if template is not None:
                    self.templates[name] = template
                    self.logger.info(f"Template '{name}' carregado com sucesso.")
                else:
                    self.logger.error(f"Erro ao carregar imagem: {full_path}")

    def capture_screen(self) -> np.ndarray:
        monitor = self.sct.monitors[self.config.monitor_index]
        sct_img = self.sct.grab(monitor)
        frame = np.array(sct_img)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def find_template(
        self,
        template_name: str,
        threshold: Optional[float] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[Tuple[int, int, int, int]]:
        if template_name not in self.templates:
            return None

        thresh = threshold if threshold is not None else self.config.confidence
        screen = self.capture_screen()

        if region:
            rx, ry, rw, rh = region
            screen = screen[ry : ry + rh, rx : rx + rw]
            offset_x, offset_y = rx, ry
        else:
            offset_x, offset_y = 0, 0

        template = self.templates[template_name]
        th, tw = template.shape[:2]

        if screen.shape[0] < th or screen.shape[1] < tw:
            return None

        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= thresh:
            top_left = max_loc
            center_x = top_left[0] + tw // 2 + offset_x
            center_y = top_left[1] + th // 2 + offset_y
            return (center_x, center_y, tw, th)

        return None

    def template_exists(self, template_name: str, threshold: Optional[float] = None) -> bool:
        return self.find_template(template_name, threshold=threshold) is not None

    def wait_template(
        self,
        template_name: str,
        timeout: float = 10.0,
        threshold: Optional[float] = None,
        check_interval: float = 0.2,
    ) -> Optional[Tuple[int, int, int, int]]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            res = self.find_template(template_name, threshold)
            if res is not None:
                return res
            time.sleep(check_interval)
        return None

    def click_template(
        self, template_name: str, threshold: Optional[float] = None, timeout: float = 0.0
    ) -> bool:
        if timeout > 0:
            match = self.wait_template(template_name, timeout=timeout, threshold=threshold)
        else:
            match = self.find_template(template_name, threshold=threshold)

        if match:
            x, y, _, _ = match
            self.input_ctrl.click_position(x, y)
            self.logger.info(f"Clique realizado no template '{template_name}' em ({x}, {y})")
            return True

        return False

    def save_region_as_template(
        self, x: int, y: int, width: int, height: int, template_name: str
    ) -> bool:
        screen = self.capture_screen()
        h, w = screen.shape[:2]

        if x < 0 or y < 0 or x + width > w or y + height > h:
            self.logger.error("Região fora dos limites da tela.")
            return False

        crop = screen[y : y + height, x : x + width]
        file_path = os.path.join(self.config.templates_path, f"{template_name}.png")
        cv2.imwrite(file_path, crop)
        self.logger.info(f"Novo template salvo em: {file_path}")
        self.load_templates()
        return True

    def capture_template_interactive(self, template_name: str) -> bool:
        time.sleep(2.0)
        screen = self.capture_screen()

        win_name = "Selecione o elemento com o mouse e aperte ENTER (ESC para cancelar)"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(win_name, cv2.WND_PROP_TOPMOST, 1)

        rect = cv2.selectROI(win_name, screen, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(win_name)

        x, y, w, h = map(int, rect)
        if w > 0 and h > 0:
            crop = screen[y : y + h, x : x + w]
            file_path = os.path.join(self.config.templates_path, f"{template_name}.png")
            cv2.imwrite(file_path, crop)
            self.logger.info(f"Template '{template_name}' salvo com sucesso em {file_path}!")
            self.load_templates()
            return True
        return False