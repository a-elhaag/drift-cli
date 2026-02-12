"""Configuration management for Drift CLI."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class DriftConfig(BaseModel):
    """Configuration for Drift CLI."""

    model: str = "qwen2.5-coder:1.5b"
    ollama_url: str = "http://localhost:11434"
    temperature: float = 0.1
    top_p: float = 0.9
    max_history: int = 100
    auto_snapshot: bool = True


class ConfigManager:
    """Manages Drift configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".drift" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)

    def load(self) -> DriftConfig:
        """Load configuration from file or return defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                return DriftConfig(**data)
            except Exception:
                # If config is corrupted, return defaults
                return DriftConfig()
        return DriftConfig()

    def save(self, config: DriftConfig):
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            json.dump(config.model_dump(), f, indent=2)

    def update(self, **kwargs):
        """Update specific config values."""
        config = self.load()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        self.save(config)
