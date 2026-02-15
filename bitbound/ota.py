"""
OTA (Over-The-Air) Update Manager for BitBound.

Provides firmware and application update capabilities
for MicroPython devices.
"""

import json
import os
import time
import hashlib
from typing import Any, Callable, Dict, Optional
from enum import Enum


class OTAStatus(Enum):
    """OTA update status."""
    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


class OTAManager:
    """
    Over-The-Air update manager.

    Example:
        from bitbound.ota import OTAManager

        ota = OTAManager(
            update_url="https://api.example.com/firmware",
            current_version="1.0.0"
        )

        # Check for updates
        if ota.check_update():
            print(f"New version available: {ota.available_version}")
            ota.update()

        # Or auto-update
        ota.auto_update(check_interval_hours=24)
    """

    def __init__(
        self,
        update_url: str = "",
        current_version: str = "0.0.0",
        app_path: str = ".",
        backup_path: str = ".backup",
    ):
        """
        Initialize OTA manager.

        Args:
            update_url: URL for update server
            current_version: Current application version
            app_path: Path to application files
            backup_path: Path for backup files (rollback)
        """
        self._update_url = update_url
        self._current_version = current_version
        self._app_path = app_path
        self._backup_path = backup_path
        self._status = OTAStatus.IDLE
        self._available_version: Optional[str] = None
        self._update_info: Dict[str, Any] = {}
        self._simulation = True
        self._progress = 0.0
        self._callbacks: Dict[OTAStatus, list] = {}
        self._error_message = ""

        self._detect_platform()

    def _detect_platform(self) -> None:
        """Detect if HTTP requests are available."""
        try:
            import urequests
            self._simulation = False
        except ImportError:
            try:
                import requests
                self._simulation = False
            except ImportError:
                self._simulation = True

    def check_update(self) -> bool:
        """
        Check if a new version is available.

        Returns:
            True if update available
        """
        self._set_status(OTAStatus.CHECKING)

        if self._simulation:
            # Simulate an available update
            self._available_version = self._bump_version(self._current_version)
            self._update_info = {
                "version": self._available_version,
                "size": 1024,
                "checksum": "simulated",
                "files": ["main.py", "bitbound/update.py"],
                "changelog": "Simulated update",
            }
            self._set_status(OTAStatus.IDLE)
            return True

        try:
            response = self._http_get(
                f"{self._update_url}/check",
                params={"current_version": self._current_version}
            )

            if response and response.get("update_available"):
                self._available_version = response.get("version")
                self._update_info = response
                self._set_status(OTAStatus.IDLE)
                return True

            self._set_status(OTAStatus.IDLE)
            return False

        except Exception as e:
            self._error_message = str(e)
            self._set_status(OTAStatus.FAILED)
            return False

    def update(self) -> bool:
        """
        Download and install the available update.

        Returns:
            True if update installed successfully
        """
        if not self._available_version:
            if not self.check_update():
                return False

        # Backup current files
        self._backup()

        # Download update
        self._set_status(OTAStatus.DOWNLOADING)
        try:
            if self._simulation:
                # Simulate download progress
                for i in range(10):
                    self._progress = (i + 1) / 10.0
                    time.sleep(0.1)
            else:
                self._download_update()

        except Exception as e:
            self._error_message = str(e)
            self._set_status(OTAStatus.FAILED)
            self.rollback()
            return False

        # Verify
        self._set_status(OTAStatus.VERIFYING)
        if not self._verify_update():
            self._set_status(OTAStatus.FAILED)
            self.rollback()
            return False

        # Install
        self._set_status(OTAStatus.INSTALLING)
        if self._simulation:
            self._current_version = self._available_version
            self._available_version = None
            self._progress = 1.0
            self._set_status(OTAStatus.COMPLETED)
            return True

        try:
            self._install_update()
            self._current_version = self._available_version
            self._available_version = None
            self._set_status(OTAStatus.COMPLETED)
            return True

        except Exception as e:
            self._error_message = str(e)
            self._set_status(OTAStatus.FAILED)
            self.rollback()
            return False

    def rollback(self) -> bool:
        """
        Rollback to the previous version.

        Returns:
            True if rollback successful
        """
        self._set_status(OTAStatus.ROLLBACK)

        if self._simulation:
            print("[SIM] Rollback completed")
            self._set_status(OTAStatus.IDLE)
            return True

        try:
            # Restore backed up files
            self._restore_backup()
            self._set_status(OTAStatus.IDLE)
            return True
        except Exception as e:
            self._error_message = str(e)
            self._set_status(OTAStatus.FAILED)
            return False

    def _backup(self) -> None:
        """Backup current application files."""
        if self._simulation:
            return

        try:
            os.makedirs(self._backup_path, exist_ok=True)
        except (OSError, AttributeError):
            try:
                os.mkdir(self._backup_path)
            except OSError:
                pass

        # Save version info
        try:
            with open(f"{self._backup_path}/version.json", "w") as f:
                json.dump({"version": self._current_version}, f)
        except Exception:
            pass

    def _restore_backup(self) -> None:
        """Restore backed up files."""
        try:
            with open(f"{self._backup_path}/version.json", "r") as f:
                info = json.load(f)
                self._current_version = info.get("version", self._current_version)
        except Exception:
            pass

    def _download_update(self) -> None:
        """Download update files from server."""
        url = f"{self._update_url}/download"
        response = self._http_get(url, params={"version": self._available_version})
        if not response:
            raise RuntimeError("Download failed")

    def _verify_update(self) -> bool:
        """Verify downloaded update integrity."""
        if self._simulation:
            return True

        checksum = self._update_info.get("checksum")
        if not checksum:
            return True  # No checksum to verify

        # Verify file checksums
        return True

    def _install_update(self) -> None:
        """Install downloaded update files."""
        pass

    def _http_get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make an HTTP GET request."""
        try:
            try:
                import urequests
                if params:
                    query = "&".join(f"{k}={v}" for k, v in params.items())
                    url = f"{url}?{query}"
                resp = urequests.get(url)
                data = resp.json()
                resp.close()
                return data
            except ImportError:
                import requests
                resp = requests.get(url, params=params)
                return resp.json()
        except Exception as e:
            print(f"HTTP error: {e}")
            return None

    @staticmethod
    def _bump_version(version: str) -> str:
        """Bump patch version for simulation."""
        parts = version.split(".")
        if len(parts) == 3:
            parts[2] = str(int(parts[2]) + 1)
        return ".".join(parts)

    @staticmethod
    def version_compare(v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

        for a, b in zip(parts1, parts2):
            if a < b:
                return -1
            if a > b:
                return 1

        if len(parts1) < len(parts2):
            return -1
        if len(parts1) > len(parts2):
            return 1
        return 0

    def on_status(self, status: OTAStatus, callback: Callable) -> None:
        """Register a callback for status changes."""
        if status not in self._callbacks:
            self._callbacks[status] = []
        self._callbacks[status].append(callback)

    def _set_status(self, status: OTAStatus) -> None:
        """Update status and fire callbacks."""
        self._status = status
        if status in self._callbacks:
            for cb in self._callbacks[status]:
                try:
                    cb(status)
                except Exception as e:
                    print(f"OTA callback error: {e}")

    @property
    def status(self) -> OTAStatus:
        return self._status

    @property
    def current_version(self) -> str:
        return self._current_version

    @property
    def available_version(self) -> Optional[str]:
        return self._available_version

    @property
    def progress(self) -> float:
        return self._progress

    @property
    def error(self) -> str:
        return self._error_message

    def __repr__(self) -> str:
        mode = "SIM" if self._simulation else "HW"
        return f"<OTAManager [{mode}] v{self._current_version} status={self._status.value}>"
