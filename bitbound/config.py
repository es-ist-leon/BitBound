"""
Configuration management for BitBound.

Loads and manages device/project configurations from JSON files.
Supports environment-specific profiles and default overrides.
"""

import json
import os
from typing import Any, Dict, List, Optional


# Default device profiles
DEVICE_PROFILES: Dict[str, Dict[str, Any]] = {
    "esp32": {
        "board": "ESP32",
        "i2c": {"scl": 22, "sda": 21},
        "spi": {"sck": 18, "mosi": 23, "miso": 19},
        "uart": {"tx": 17, "rx": 16},
        "onewire": {"pin": 4},
        "builtin_led": 2,
    },
    "esp32s3": {
        "board": "ESP32-S3",
        "i2c": {"scl": 9, "sda": 8},
        "spi": {"sck": 12, "mosi": 11, "miso": 13},
        "uart": {"tx": 43, "rx": 44},
        "onewire": {"pin": 4},
        "builtin_led": 48,
    },
    "esp32c3": {
        "board": "ESP32-C3",
        "i2c": {"scl": 9, "sda": 8},
        "spi": {"sck": 4, "mosi": 6, "miso": 5},
        "uart": {"tx": 21, "rx": 20},
        "onewire": {"pin": 3},
        "builtin_led": 8,
    },
    "esp8266": {
        "board": "ESP8266",
        "i2c": {"scl": 5, "sda": 4},
        "spi": {"sck": 14, "mosi": 13, "miso": 12},
        "uart": {"tx": 1, "rx": 3},
        "onewire": {"pin": 2},
        "builtin_led": 2,
    },
    "rpi_pico": {
        "board": "Raspberry Pi Pico",
        "i2c": {"scl": 1, "sda": 0},
        "spi": {"sck": 2, "mosi": 3, "miso": 4},
        "uart": {"tx": 0, "rx": 1},
        "onewire": {"pin": 15},
        "builtin_led": 25,
    },
    "rpi_pico_w": {
        "board": "Raspberry Pi Pico W",
        "i2c": {"scl": 1, "sda": 0},
        "spi": {"sck": 2, "mosi": 3, "miso": 4},
        "uart": {"tx": 0, "rx": 1},
        "onewire": {"pin": 15},
        "builtin_led": "LED",
    },
}


class Config:
    """
    Configuration manager for BitBound projects.

    Example:
        from bitbound.config import Config

        # Load from file
        config = Config.from_file("config.json")

        # Or create programmatically
        config = Config(board="esp32")
        config.set("wifi.ssid", "MyNetwork")
        config.set("wifi.password", "secret")

        # Access nested values
        ssid = config.get("wifi.ssid")
        pins = config.get("i2c", default={"scl": 22, "sda": 21})
    """

    def __init__(
        self,
        data: Optional[Dict[str, Any]] = None,
        board: Optional[str] = None
    ):
        """
        Initialize config.

        Args:
            data: Initial configuration dictionary
            board: Board profile name (e.g., "esp32", "rpi_pico")
        """
        self._data: Dict[str, Any] = {}

        # Load board profile if specified
        if board:
            profile = DEVICE_PROFILES.get(board.lower())
            if profile:
                self._data.update(profile)
            else:
                raise ValueError(
                    f"Unknown board: {board}. "
                    f"Available: {list(DEVICE_PROFILES.keys())}"
                )

        # Override with provided data
        if data:
            self._deep_merge(self._data, data)

    @classmethod
    def from_file(cls, path: str, board: Optional[str] = None) -> "Config":
        """
        Load configuration from a JSON file.

        Args:
            path: Path to JSON config file
            board: Optional board profile to use as base

        Returns:
            Config instance
        """
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls(data=data, board=board)
        except FileNotFoundError:
            print(f"Config file not found: {path}")
            return cls(board=board)
        except json.JSONDecodeError as e:
            print(f"Config parse error: {e}")
            return cls(board=board)

    def save(self, path: str) -> bool:
        """
        Save configuration to a JSON file.

        Args:
            path: Path to save to

        Returns:
            True if saved
        """
        try:
            with open(path, "w") as f:
                json.dump(self._data, f, indent=2)
            return True
        except Exception as e:
            print(f"Config save error: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Config key (e.g., "wifi.ssid" or "i2c.scl")
            default: Default value if not found

        Returns:
            Config value
        """
        parts = key.split(".")
        value = self._data

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key: Config key (e.g., "wifi.ssid")
            value: Value to set
        """
        parts = key.split(".")
        target = self._data

        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value

    def has(self, key: str) -> bool:
        """Check if a config key exists."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """Delete a config key."""
        parts = key.split(".")
        target = self._data

        for part in parts[:-1]:
            if isinstance(target, dict) and part in target:
                target = target[part]
            else:
                return False

        if isinstance(target, dict) and parts[-1] in target:
            del target[parts[-1]]
            return True
        return False

    def merge(self, other: Dict[str, Any]) -> None:
        """Merge another dictionary into the config."""
        self._deep_merge(self._data, other)

    def to_dict(self) -> Dict[str, Any]:
        """Get the full config as a dictionary."""
        return dict(self._data)

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    @staticmethod
    def available_boards() -> List[str]:
        """Get list of available board profiles."""
        return list(DEVICE_PROFILES.keys())

    @staticmethod
    def get_board_profile(board: str) -> Optional[Dict[str, Any]]:
        """Get a board profile by name."""
        return DEVICE_PROFILES.get(board.lower())

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __repr__(self) -> str:
        board = self._data.get("board", "unknown")
        return f"<Config board={board} keys={len(self._data)}>"
