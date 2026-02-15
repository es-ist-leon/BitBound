"""Tests for WiFi Manager."""

import pytest
from bitbound.network.wifi import WiFiManager, WiFiConfig, WiFiStatus, WiFiMode, WiFiNetwork


class TestWiFiManager:
    def test_create_manager(self):
        wifi = WiFiManager()
        assert wifi.status == WiFiStatus.IDLE
        assert not wifi.is_connected

    def test_connect_simulation(self):
        wifi = WiFiManager()
        result = wifi.connect("TestNetwork", "password")
        assert result is True
        assert wifi.is_connected
        assert wifi.status == WiFiStatus.CONNECTED

    def test_disconnect(self):
        wifi = WiFiManager()
        wifi.connect("TestNetwork", "password")
        wifi.disconnect()
        assert not wifi.is_connected
        assert wifi.status == WiFiStatus.DISCONNECTED

    def test_ip_address(self):
        wifi = WiFiManager()
        wifi.connect("TestNetwork", "password")
        assert wifi.ip_address is not None
        assert "." in wifi.ip_address

    def test_mac_address(self):
        wifi = WiFiManager()
        assert wifi.mac_address != ""

    def test_rssi(self):
        wifi = WiFiManager()
        wifi.connect("TestNetwork", "password")
        assert wifi.rssi < 0  # Simulated RSSI

    def test_scan(self):
        wifi = WiFiManager()
        networks = wifi.scan()
        assert len(networks) > 0
        assert isinstance(networks[0], WiFiNetwork)
        assert networks[0].ssid != ""

    def test_ifconfig(self):
        wifi = WiFiManager()
        wifi.connect("TestNetwork", "password")
        cfg = wifi.ifconfig
        assert "ip" in cfg
        assert "subnet" in cfg

    def test_status_callback(self):
        events = []
        wifi = WiFiManager()
        wifi.on_status_change(WiFiStatus.CONNECTED, lambda o, n: events.append(n))
        wifi.connect("TestNetwork", "password")
        assert WiFiStatus.CONNECTED in events

    def test_connect_requires_ssid(self):
        wifi = WiFiManager()
        with pytest.raises(ValueError):
            wifi.connect()

    def test_repr(self):
        wifi = WiFiManager()
        assert "WiFiManager" in repr(wifi)

    def test_start_ap(self):
        wifi = WiFiManager()
        assert wifi.start_ap("TestAP") is True

    def test_ensure_connected(self):
        wifi = WiFiManager()
        wifi.connect("TestNetwork", "password")
        assert wifi.ensure_connected() is True


class TestWiFiConfig:
    def test_default_config(self):
        config = WiFiConfig()
        assert config.ssid == ""
        assert config.mode == WiFiMode.STATION
        assert config.auto_reconnect is True

    def test_custom_config(self):
        config = WiFiConfig(ssid="MyNet", password="pass", timeout=30)
        wifi = WiFiManager(config=config)
        assert wifi.connect() is True
