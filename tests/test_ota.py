"""Tests for OTA Manager."""

import pytest
from bitbound.ota import OTAManager, OTAStatus


class TestOTAManager:
    def _sim_ota(self, version="1.0.0"):
        """Create an OTAManager forced into simulation mode."""
        ota = OTAManager(current_version=version)
        ota._simulation = True
        return ota

    def test_create_manager(self):
        ota = OTAManager(current_version="1.0.0")
        assert ota.current_version == "1.0.0"
        assert ota.status == OTAStatus.IDLE

    def test_check_update(self):
        ota = self._sim_ota()
        assert ota.check_update() is True
        assert ota.available_version is not None

    def test_update_simulation(self):
        ota = self._sim_ota()
        result = ota.update()
        assert result is True
        assert ota.status == OTAStatus.COMPLETED
        assert ota.current_version == "1.0.1"

    def test_rollback(self):
        ota = self._sim_ota()
        assert ota.rollback() is True
        assert ota.status == OTAStatus.IDLE

    def test_version_compare(self):
        assert OTAManager.version_compare("1.0.0", "1.0.1") == -1
        assert OTAManager.version_compare("1.0.1", "1.0.0") == 1
        assert OTAManager.version_compare("1.0.0", "1.0.0") == 0
        assert OTAManager.version_compare("2.0.0", "1.9.9") == 1

    def test_progress(self):
        ota = self._sim_ota()
        assert ota.progress == 0.0
        ota.update()
        assert ota.progress == 1.0

    def test_status_callback(self):
        statuses = []
        ota = self._sim_ota()
        ota.on_status(OTAStatus.COMPLETED, lambda s: statuses.append(s))
        ota.update()
        assert OTAStatus.COMPLETED in statuses

    def test_bump_version(self):
        assert OTAManager._bump_version("1.0.0") == "1.0.1"
        assert OTAManager._bump_version("0.9.9") == "0.9.10"

    def test_repr(self):
        ota = OTAManager(current_version="1.0.0")
        assert "OTAManager" in repr(ota)
        assert "1.0.0" in repr(ota)
