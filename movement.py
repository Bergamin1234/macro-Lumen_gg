import time
import random
import logging
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
        pattern = self.config.movement_pattern.lower()

        if pattern == "zigzag":
            return self._step_zigzag(check_interrupt)
        elif pattern == "square":
            return self._step_square(check_interrupt)
        elif pattern == "random":
            return self._step_random(check_interrupt)
        elif pattern == "custom":
            return self._step_custom(check_interrupt)
        else:
            return self._step_zigzag(check_interrupt)

    def _walk_dir(self, key: str, duration: float, check_interrupt: Callable[[], bool]) -> bool:
        self.input_ctrl.hold_key(key)
        start_time = time.time()
        interrupted = False

        while time.time() - start_time < duration:
            if check_interrupt():
                interrupted = True
                break
            time.sleep(0.05)

        self.input_ctrl.release_key(key)
        return interrupted

    def _step_zigzag(self, check_interrupt: Callable[[], bool]) -> bool:
        steps = ["left", "right"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_square(self, check_interrupt: Callable[[], bool]) -> bool:
        steps = ["up", "right", "down", "left"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_random(self, check_interrupt: Callable[[], bool]) -> bool:
        direction = random.choice(["up", "down", "left", "right"])
        dur = random.uniform(0.2, 0.6)
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    def _step_custom(self, check_interrupt: Callable[[], bool]) -> bool:
        steps = ["up", "down", "left", "right"]
        direction = steps[self.step_index % len(steps)]
        self.step_index += 1
        dur = getattr(self.config.directions_time, direction, self.config.step_duration)
        return self._walk_dir(self._dir_to_key(direction), dur, check_interrupt)

    @staticmethod
    def _dir_to_key(direction: str) -> str:
        mapping = {"up": "w", "down": "s", "left": "a", "right": "d"}
        return mapping.get(direction, "w")