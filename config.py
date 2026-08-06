import json
import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class KeyBindings:
    up: str = "w"
    down: str = "s"
    left: str = "a"
    right: str = "d"


@dataclass
class Config:
    window_title: str = "Lumena.gg"
    confidence: float = 0.8
    templates_dir: str = "templates"
    logs_dir: str = "logs"
    movement_pattern: str = "zigzag"
    step_duration: float = 0.35
    battle_timeout: float = 35.0
    attack_delay: float = 0.8
    monitor: int = 1
    keys: KeyBindings = field(default_factory=KeyBindings)

    @classmethod
    def load_from_json(cls, filepath: str = "settings.json") -> "Config":
        if not os.path.exists(filepath):
            config = cls()
            config.save_to_json(filepath)
            return config

        with open(filepath, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        keys_data = data.pop("keys", {})
        keys = KeyBindings(**keys_data)
        return cls(keys=keys, **data)

    def save_to_json(self, filepath: str = "settings.json") -> None:
        data = {
            "window_title": self.window_title,
            "confidence": self.confidence,
            "templates_dir": self.templates_dir,
            "logs_dir": self.logs_dir,
            "movement_pattern": self.movement_pattern,
            "step_duration": self.step_duration,
            "battle_timeout": self.battle_timeout,
            "attack_delay": self.attack_delay,
            "monitor": self.monitor,
            "keys": {
                "up": self.keys.up,
                "down": self.keys.down,
                "left": self.keys.left,
                "right": self.keys.right
            }
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)