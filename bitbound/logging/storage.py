"""
Storage abstraction for BitBound.

Provides filesystem-agnostic storage for configuration and data
on both MicroPython and desktop.
"""

import json
import os
from typing import Any, Dict, List, Optional


class Storage:
    """
    Abstract storage interface.

    Provides a key-value and file-based storage API that works
    on both MicroPython (flash filesystem) and desktop.
    """

    def __init__(self, base_path: str = "."):
        self._base_path = base_path
        self._ensure_dir(base_path)

    def _ensure_dir(self, path: str) -> None:
        """Ensure a directory exists."""
        try:
            os.makedirs(path, exist_ok=True)
        except (OSError, AttributeError):
            # MicroPython may not support exist_ok
            try:
                os.mkdir(path)
            except OSError:
                pass

    def _full_path(self, key: str) -> str:
        """Get full path for a key."""
        return f"{self._base_path}/{key}"

    def save(self, key: str, data: Any) -> bool:
        """
        Save data to storage.

        Args:
            key: Storage key (used as filename)
            data: Data to save (will be JSON-serialized)

        Returns:
            True if saved successfully
        """
        try:
            path = self._full_path(key)
            with open(path, "w") as f:
                json.dump(data, f)
            return True
        except Exception as e:
            print(f"Storage save error: {e}")
            return False

    def load(self, key: str, default: Any = None) -> Any:
        """
        Load data from storage.

        Args:
            key: Storage key
            default: Default value if key not found

        Returns:
            Loaded data or default
        """
        try:
            path = self._full_path(key)
            with open(path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, OSError):
            return default
        except Exception as e:
            print(f"Storage load error: {e}")
            return default

    def delete(self, key: str) -> bool:
        """
        Delete data from storage.

        Args:
            key: Storage key

        Returns:
            True if deleted
        """
        try:
            path = self._full_path(key)
            os.remove(path)
            return True
        except (FileNotFoundError, OSError):
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""
        try:
            path = self._full_path(key)
            os.stat(path)
            return True
        except (FileNotFoundError, OSError):
            return False

    def list_keys(self) -> List[str]:
        """List all keys in storage."""
        try:
            return [f for f in os.listdir(self._base_path)
                    if not f.startswith(".")]
        except OSError:
            return []

    def clear(self) -> None:
        """Remove all stored data."""
        for key in self.list_keys():
            self.delete(key)

    def __repr__(self) -> str:
        return f"<Storage path={self._base_path}>"


class FileStorage(Storage):
    """
    File-based storage with support for raw file operations.

    Extends Storage with methods for reading/writing raw files,
    binary data, and directory management.
    """

    def write_text(self, path: str, content: str) -> bool:
        """Write text content to a file."""
        try:
            full_path = self._full_path(path)
            with open(full_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"FileStorage write error: {e}")
            return False

    def read_text(self, path: str) -> Optional[str]:
        """Read text content from a file."""
        try:
            full_path = self._full_path(path)
            with open(full_path, "r") as f:
                return f.read()
        except (FileNotFoundError, OSError):
            return None

    def write_bytes(self, path: str, data: bytes) -> bool:
        """Write binary data to a file."""
        try:
            full_path = self._full_path(path)
            with open(full_path, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"FileStorage write_bytes error: {e}")
            return False

    def read_bytes(self, path: str) -> Optional[bytes]:
        """Read binary data from a file."""
        try:
            full_path = self._full_path(path)
            with open(full_path, "rb") as f:
                return f.read()
        except (FileNotFoundError, OSError):
            return None

    def append_text(self, path: str, content: str) -> bool:
        """Append text to a file."""
        try:
            full_path = self._full_path(path)
            with open(full_path, "a") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"FileStorage append error: {e}")
            return False

    def file_size(self, path: str) -> int:
        """Get file size in bytes."""
        try:
            full_path = self._full_path(path)
            return os.stat(full_path)[6]  # st_size works on MicroPython too
        except (FileNotFoundError, OSError):
            return 0

    def mkdir(self, path: str) -> bool:
        """Create a directory."""
        try:
            self._ensure_dir(self._full_path(path))
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"<FileStorage path={self._base_path}>"
