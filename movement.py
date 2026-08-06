import logging
import random
import time
from typing import Callable

from config import Config
from input_controller import InputController


class MovementManager:
    def __init__(self, config: Config, input_ctrl: InputController) -> None:
        self.config = config
        self.input_ctrl = input_ctrl
        self.logger = logging.getLogger("LumenaMacro.Movement")
        self.step_index = 0

    def execute_step(self, check_interrupt: Callable[[], bool]) -> bool:
        """Executa um passo do padrão configurado."""
        pattern = self.config.movement_pattern.lower()

        if pattern in ["zigzag", "zig-zag"]:
            return self._step_zigzag(check_interrupt)
        elif pattern in ["square", "quadrado", "circle", "circulo"]:
            return self._step_circle(check_interrupt)
        elif pattern in ["random", "aleatorio"]:
            return self._step_random(check_interrupt)
        else:
            return self._step_zigzag(check_interrupt)

    def _walk_dir(self, key: str, duration: float, check_interrupt: Callable[[], bool]) -> bool:
        """Pressiona a tecla de movimento enviando pulsos contínuos para o navegador."""
        start_time = time.time()
        interrupted = False

        try:
            self.input_ctrl.hold_key(key)
            while time.time() - start_time < duration:
                if check_interrupt():
                    interrupted = True
                    break
                # Re-envia o sinal de tecla para navegadores HTML5 que exigem repetição
                self.input_ctrl.hold_key(key)
                time.sleep(0.05)
        finally:
            self.input_ctrl.release_key(key)

        return interrupted

    def _step_zigzag(self, check_interrupt: Callable[[], bool]) -> bool:
        """Movimento alternado: Esquerda (A) <-> Direita (D)."""
        steps = ["left", "right"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        self.logger.info(f"Caminhando: {direction.upper()} por {dur}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_circle(self, check_interrupt: Callable[[], bool]) -> bool:
        """Movimento em círculo/quadrado: Cima (W) -> Direita (D) -> Baixo (S) -> Esquerda (A)."""
        steps = ["up", "right", "down", "left"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        self.logger.info(f"Caminhando em círculo: {direction.upper()} por {dur}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_random(self, check_interrupt: Callable[[], bool]) -> bool:
        """Movimento aleatório controlado."""
        direction = random.choice(["up", "down", "left", "right"])
        dur = random.uniform(0.3, 0.7)
        self.logger.info(f"Caminhando aleatório: {direction.upper()} por {dur:.1f}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    @staticmethod
    def _dir_to_key(direction: str) -> str:
        mapping = {"up": "w", "down": "s", "left": "a", "right": "d"}
        return mapping.get(direction, "w")