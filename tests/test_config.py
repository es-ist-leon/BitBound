"""Tests for Configuration Management."""

import os
import json
import tempfile
import pytest
from bitbound.config import Config, DEVICE_PROFILES


class TestConfig:
    def test_create_empty(self):
        config = Config()
        assert config.to_dict() == {}

    def test_create_with_board(self):
        config = Config(board="esp32")
        assert config.get("board") == "ESP32"
        assert config.get("i2c.scl") == 22
        assert config.get("i2c.sda") == 21

    def test_create_with_data(self):
        config = Config(data={"project": {"name": "test"}})
        assert config.get("project.name") == "test"

    def test_unknown_board(self):
        with pytest.raises(ValueError):
            Config(board="unknown_board")

    def test_get_set(self):
        config = Config()
        config.set("wifi.ssid", "MyNetwork")
        assert config.get("wifi.ssid") == "MyNetwork"

    def test_get_default(self):
        config = Config()
        assert config.get("nonexistent", "default") == "default"

    def test_nested_set(self):
        config = Config()
        config.set("a.b.c", 42)
        assert config.get("a.b.c") == 42

    def test_has(self):
        config = Config()
        config.set("key", "value")
        assert config.has("key") is True
        assert config.has("missing") is False

    def test_delete(self):
        config = Config()
        config.set("key", "value")
        assert config.delete("key") is True
        assert not config.has("key")

    def test_delete_nonexistent(self):
        config = Config()
        assert config.delete("nonexistent") is False

    def test_merge(self):
        config = Config(data={"a": 1, "b": {"c": 2}})
        config.merge({"b": {"d": 3}, "e": 4})
        assert config.get("a") == 1
        assert config.get("b.c") == 2
        assert config.get("b.d") == 3
        assert config.get("e") == 4

    def test_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"project": "test", "wifi": {"ssid": "Net"}}, f)
            f.flush()
            config = Config.from_file(f.name)
            assert config.get("project") == "test"
            assert config.get("wifi.ssid") == "Net"
        os.unlink(f.name)

    def test_save(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        config = Config(data={"test": "data"})
        assert config.save(path) is True

        loaded = Config.from_file(path)
        assert loaded.get("test") == "data"
        os.unlink(path)

    def test_from_file_missing(self):
        config = Config.from_file("nonexistent_file.json")
        assert config.to_dict() == {}

    def test_available_boards(self):
        boards = Config.available_boards()
        assert "esp32" in boards
        assert "rpi_pico" in boards

    def test_get_board_profile(self):
        profile = Config.get_board_profile("esp32")
        assert profile is not None
        assert profile["board"] == "ESP32"

    def test_dict_access(self):
        config = Config(data={"key": "value"})
        assert config["key"] == "value"

    def test_dict_set(self):
        config = Config()
        config["key"] = "value"
        assert config.get("key") == "value"

    def test_contains(self):
        config = Config(data={"key": "value"})
        assert "key" in config
        assert "missing" not in config

    def test_dict_access_missing(self):
        config = Config()
        with pytest.raises(KeyError):
            _ = config["missing"]

    def test_repr(self):
        config = Config(board="esp32")
        assert "Config" in repr(config)

    def test_board_profiles_complete(self):
        """Ensure all board profiles have required keys."""
        required_keys = {"board", "i2c", "builtin_led"}
        for name, profile in DEVICE_PROFILES.items():
            for key in required_keys:
                assert key in profile, f"{name} missing {key}"
