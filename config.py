import json
import os
from dataclasses import dataclass, asdict, field


@dataclass
class DirectionsTime:
    up: float = 0.5
    down: float = 0.5
    left: float = 0.5
    right: float = 0.5


@dataclass
class Config:
    window_name: str = "Lumena.gg"
    monitor_index: int = 1
    confidence: float = 0.8
    templates_path: str = "templates"
    logs_path: str = "logs"
    movement_pattern: str = "zigzag"
    step_duration: float = 0.4
    directions_time: DirectionsTime = field(default_factory=DirectionsTime)
    attack_delay: float = 0.5
    battle_timeout: float = 30.0
    max_stuck_seconds: float = 60.0

    @classmethod
    def load_from_json(cls, filepath: str = "settings.json") -> "Config":
        if not os.path.exists(filepath):
            config = cls()
            config.save_to_json(filepath)
            return config

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "directions_time" in data and isinstance(data["directions_time"], dict):
            data["directions_time"] = DirectionsTime(**data["directions_time"])

        return cls(**data)

    def save_to_json(self, filepath: str = "settings.json") -> None:
        data = asdict(self)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)