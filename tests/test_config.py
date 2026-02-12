"""Tests for configuration management."""

import json
import pytest
from pathlib import Path

from drift_cli.core.config import DriftConfig, ConfigManager


class TestDriftConfig:
    """Test DriftConfig model defaults and validation."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = DriftConfig()
        assert config.model == "qwen2.5-coder:1.5b"
        assert config.ollama_url == "http://localhost:11434"
        assert config.temperature == 0.1
        assert config.top_p == 0.9
        assert config.max_history == 100
        assert config.auto_snapshot is True

    def test_custom_values(self):
        """Config should accept custom values."""
        config = DriftConfig(
            model="llama3:8b",
            temperature=0.5,
            max_history=50,
            auto_snapshot=False,
        )
        assert config.model == "llama3:8b"
        assert config.temperature == 0.5
        assert config.max_history == 50
        assert config.auto_snapshot is False

    def test_serialization_roundtrip(self):
        """Config should survive JSON serialization."""
        original = DriftConfig(model="codellama:7b", temperature=0.3)
        data = original.model_dump()
        restored = DriftConfig(**data)
        assert restored.model == original.model
        assert restored.temperature == original.temperature


class TestConfigManager:
    """Test ConfigManager load/save/update."""

    def test_load_returns_defaults_when_no_file(self, tmp_path):
        """Loading from nonexistent path returns defaults."""
        manager = ConfigManager(config_path=tmp_path / "nonexistent" / "config.json")
        config = manager.load()
        assert config.model == "qwen2.5-coder:1.5b"

    def test_save_and_load(self, tmp_path):
        """Saved config should be loadable."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path=config_path)

        config = DriftConfig(model="deepseek-coder:6.7b", temperature=0.7)
        manager.save(config)

        loaded = manager.load()
        assert loaded.model == "deepseek-coder:6.7b"
        assert loaded.temperature == 0.7

    def test_update_specific_fields(self, tmp_path):
        """Update should change only specified fields."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path=config_path)
        manager.save(DriftConfig())

        manager.update(model="mistral:7b", temperature=0.5)

        loaded = manager.load()
        assert loaded.model == "mistral:7b"
        assert loaded.temperature == 0.5
        # Other fields unchanged
        assert loaded.max_history == 100

    def test_update_ignores_unknown_fields(self, tmp_path):
        """Update should ignore fields not in the model."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path=config_path)
        manager.save(DriftConfig())

        manager.update(nonexistent_field="value")
        loaded = manager.load()
        assert loaded.model == "qwen2.5-coder:1.5b"  # Unchanged

    def test_load_corrupted_file_returns_defaults(self, tmp_path):
        """Corrupted config file should return defaults gracefully."""
        config_path = tmp_path / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("NOT VALID JSON {{{")

        manager = ConfigManager(config_path=config_path)
        config = manager.load()
        assert config.model == "qwen2.5-coder:1.5b"

    def test_config_file_is_valid_json(self, tmp_path):
        """Saved config should produce valid, readable JSON."""
        config_path = tmp_path / "config.json"
        manager = ConfigManager(config_path=config_path)
        manager.save(DriftConfig())

        data = json.loads(config_path.read_text())
        assert "model" in data
        assert "temperature" in data
