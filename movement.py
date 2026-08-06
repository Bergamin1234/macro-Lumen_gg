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
        """Executa um passo do padrão configurado entre as 5 opções disponíveis."""
        pattern = self.config.movement_pattern.lower()

        if pattern in ["zigzag", "zig-zag"]:
            return self._step_zigzag(check_interrupt)
        elif pattern in ["square_large", "quadrado_grande", "square"]:
            return self._step_square_large(check_interrupt)
        elif pattern in ["square_small", "quadrado_pequeno"]:
            return self._step_square_small(check_interrupt)
        elif pattern in ["random", "aleatorio"]:
            return self._step_random(check_interrupt)
        elif pattern in ["custom", "vertical"]:
            return self._step_custom_vertical(check_interrupt)
        else:
            return self._step_zigzag(check_interrupt)

    def _walk_dir(self, key: str, duration: float, check_interrupt: Callable[[], bool]) -> bool:
        """Pressiona a tecla enviando pulsos contínuos para manter o boneco correndo."""
        start_time = time.time()
        interrupted = False

        try:
            self.input_ctrl.hold_key(key)
            while time.time() - start_time < duration:
                if check_interrupt():
                    interrupted = True
                    break
                self.input_ctrl.hold_key(key)
                time.sleep(0.05)
        finally:
            self.input_ctrl.release_key(key)

        return interrupted

    def _step_zigzag(self, check_interrupt: Callable[[], bool]) -> bool:
        """1. Zig-Zag: Esquerda (A) <-> Direita (D)."""
        steps = ["left", "right"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        self.logger.info(f"Caminhando [Zig-Zag]: {direction.upper()} por {dur}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_square_large(self, check_interrupt: Callable[[], bool]) -> bool:
        """2. Quadrado Grande: Passos longos (W -> D -> S -> A)."""
        steps = ["up", "right", "down", "left"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        base_dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        dur = max(base_dur, 0.8)
        self.logger.info(f"Caminhando [Quadrado Grande]: {direction.upper()} por {dur}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_square_small(self, check_interrupt: Callable[[], bool]) -> bool:
        """3. Quadrado Pequeno: Passos bem curtos e rápidos para trechos pequenos de mato."""
        steps = ["up", "right", "down", "left"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = 0.25
        self.logger.info(f"Caminhando [Quadrado Pequeno]: {direction.upper()} por {dur}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_random(self, check_interrupt: Callable[[], bool]) -> bool:
        """4. Aleatório: Direções e tempos sorteadas."""
        direction = random.choice(["up", "down", "left", "right"])
        dur = random.uniform(0.3, 0.7)
        self.logger.info(f"Caminhando [Aleatório]: {direction.upper()} por {dur:.2f}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_custom_vertical(self, check_interrupt: Callable[[], bool]) -> bool:
        """5. Cima / Baixo: Alternado vertical (W <-> S)."""
        steps = ["up", "down"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        self.logger.info(f"Caminhando [Vertical Cima/Baixo]: {direction.upper()} por {dur}s")
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    @staticmethod
    def _dir_to_key(direction: str) -> str:
        mapping = {"up": "w", "down": "s", "left": "a", "right": "d"}
        return mapping.get(direction, "w")