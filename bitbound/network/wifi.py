"""
WiFi Manager for BitBound.

Provides a simple interface for WiFi connectivity on MicroPython
and simulation on desktop.
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from enum import Enum


class WiFiMode(Enum):
    """WiFi operating modes."""
    STATION = "STA"
    ACCESS_POINT = "AP"
    BOTH = "STA_AP"


class WiFiStatus(Enum):
    """WiFi connection states."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    NO_AP_FOUND = "no_ap_found"
    WRONG_PASSWORD = "wrong_password"


@dataclass
class WiFiNetwork:
    """Represents a scanned WiFi network."""
    ssid: str
    bssid: str = ""
    channel: int = 0
    rssi: int = 0
    security: str = "WPA2"
    hidden: bool = False


@dataclass
class WiFiConfig:
    """WiFi configuration."""
    ssid: str = ""
    password: str = ""
    mode: WiFiMode = WiFiMode.STATION
    hostname: str = "bitbound"
    static_ip: Optional[str] = None
    gateway: Optional[str] = None
    subnet: Optional[str] = None
    dns: Optional[str] = None
    auto_reconnect: bool = True
    reconnect_interval: int = 5
    max_retries: int = 10
    timeout: int = 15


class WiFiManager:
    """
    High-level WiFi management.

    Example:
        from bitbound.network import WiFiManager

        wifi = WiFiManager()
        wifi.connect("MyNetwork", "password123")

        if wifi.is_connected:
            print(f"IP: {wifi.ip_address}")
    """

    def __init__(self, config: Optional[WiFiConfig] = None):
        self._config = config or WiFiConfig()
        self._status = WiFiStatus.IDLE
        self._wlan = None
        self._ap = None
        self._simulation = True
        self._callbacks: Dict[WiFiStatus, List[Callable]] = {}
        self._retry_count = 0

        # Simulation state
        self._sim_ip = "192.168.1.100"
        self._sim_mac = "AA:BB:CC:DD:EE:FF"
        self._sim_connected = False

        self._init_interface()

    def _init_interface(self) -> None:
        """Initialize the WiFi hardware interface."""
        try:
            import network
            self._wlan = network.WLAN(network.STA_IF)
            self._simulation = False
        except ImportError:
            self._simulation = True

    def connect(
        self,
        ssid: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Connect to a WiFi network.

        Args:
            ssid: Network SSID (uses config if None)
            password: Network password (uses config if None)
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        ssid = ssid or self._config.ssid
        password = password or self._config.password
        timeout = timeout or self._config.timeout

        if not ssid:
            raise ValueError("SSID must be specified")

        self._set_status(WiFiStatus.CONNECTING)

        if self._simulation:
            self._sim_connected = True
            self._set_status(WiFiStatus.CONNECTED)
            return True

        self._wlan.active(True)

        if self._config.hostname:
            try:
                self._wlan.config(dhcp_hostname=self._config.hostname)
            except Exception:
                pass

        if self._config.static_ip:
            self._wlan.ifconfig((
                self._config.static_ip,
                self._config.subnet or "255.255.255.0",
                self._config.gateway or "192.168.1.1",
                self._config.dns or "8.8.8.8"
            ))

        self._wlan.connect(ssid, password)

        start = time.time()
        while not self._wlan.isconnected():
            if time.time() - start > timeout:
                self._set_status(WiFiStatus.FAILED)
                return False
            time.sleep(0.5)

        self._set_status(WiFiStatus.CONNECTED)
        return True

    def disconnect(self) -> None:
        """Disconnect from WiFi."""
        if self._simulation:
            self._sim_connected = False
        elif self._wlan:
            self._wlan.disconnect()
            self._wlan.active(False)

        self._set_status(WiFiStatus.DISCONNECTED)

    def scan(self) -> List[WiFiNetwork]:
        """
        Scan for available WiFi networks.

        Returns:
            List of WiFiNetwork objects
        """
        if self._simulation:
            return [
                WiFiNetwork("SimNetwork_1", "AA:BB:CC:DD:EE:01", 1, -45, "WPA2"),
                WiFiNetwork("SimNetwork_2", "AA:BB:CC:DD:EE:02", 6, -60, "WPA2"),
                WiFiNetwork("OpenNetwork", "AA:BB:CC:DD:EE:03", 11, -75, "Open"),
            ]

        self._wlan.active(True)
        results = []
        for net in self._wlan.scan():
            ssid = net[0].decode("utf-8") if isinstance(net[0], bytes) else net[0]
            bssid = ":".join(f"{b:02X}" for b in net[1]) if isinstance(net[1], bytes) else str(net[1])
            results.append(WiFiNetwork(
                ssid=ssid,
                bssid=bssid,
                channel=net[2],
                rssi=net[3],
                security=str(net[4]),
                hidden=net[5] if len(net) > 5 else False,
            ))
        return results

    def start_ap(
        self,
        ssid: str = "BitBound-AP",
        password: str = "",
        channel: int = 1
    ) -> bool:
        """
        Start a WiFi Access Point.

        Args:
            ssid: AP SSID
            password: AP password (empty = open)
            channel: WiFi channel

        Returns:
            True if AP started
        """
        if self._simulation:
            return True

        try:
            import network
            self._ap = network.WLAN(network.AP_IF)
            self._ap.active(True)
            if password:
                self._ap.config(essid=ssid, password=password, channel=channel, authmode=3)
            else:
                self._ap.config(essid=ssid, channel=channel)
            return True
        except Exception as e:
            print(f"AP start error: {e}")
            return False

    def stop_ap(self) -> None:
        """Stop the Access Point."""
        if self._ap:
            self._ap.active(False)

    @property
    def is_connected(self) -> bool:
        """Check if WiFi is connected."""
        if self._simulation:
            return self._sim_connected
        return self._wlan.isconnected() if self._wlan else False

    @property
    def ip_address(self) -> Optional[str]:
        """Get the current IP address."""
        if self._simulation:
            return self._sim_ip if self._sim_connected else None
        if self._wlan and self._wlan.isconnected():
            return self._wlan.ifconfig()[0]
        return None

    @property
    def mac_address(self) -> str:
        """Get the MAC address."""
        if self._simulation:
            return self._sim_mac
        if self._wlan:
            import ubinascii
            return ubinascii.hexlify(self._wlan.config("mac"), ":").decode()
        return ""

    @property
    def rssi(self) -> int:
        """Get the signal strength (RSSI)."""
        if self._simulation:
            return -45 if self._sim_connected else 0
        if self._wlan and self._wlan.isconnected():
            try:
                return self._wlan.status("rssi")
            except Exception:
                return 0
        return 0

    @property
    def status(self) -> WiFiStatus:
        """Get current WiFi status."""
        return self._status

    @property
    def ifconfig(self) -> Dict[str, str]:
        """Get network interface configuration."""
        if self._simulation:
            if self._sim_connected:
                return {
                    "ip": self._sim_ip,
                    "subnet": "255.255.255.0",
                    "gateway": "192.168.1.1",
                    "dns": "8.8.8.8",
                }
            return {"ip": "", "subnet": "", "gateway": "", "dns": ""}
        if self._wlan:
            cfg = self._wlan.ifconfig()
            return {"ip": cfg[0], "subnet": cfg[1], "gateway": cfg[2], "dns": cfg[3]}
        return {"ip": "", "subnet": "", "gateway": "", "dns": ""}

    def on_status_change(self, status: WiFiStatus, callback: Callable) -> None:
        """Register a callback for a specific status change."""
        if status not in self._callbacks:
            self._callbacks[status] = []
        self._callbacks[status].append(callback)

    def _set_status(self, status: WiFiStatus) -> None:
        """Update status and trigger callbacks."""
        old_status = self._status
        self._status = status
        if status in self._callbacks:
            for cb in self._callbacks[status]:
                try:
                    cb(old_status, status)
                except Exception as e:
                    print(f"WiFi callback error: {e}")

    def ensure_connected(self) -> bool:
        """Reconnect if disconnected (with retry logic)."""
        if self.is_connected:
            self._retry_count = 0
            return True

        if self._retry_count >= self._config.max_retries:
            return False

        self._retry_count += 1
        return self.connect()

    def __repr__(self) -> str:
        mode = "SIM" if self._simulation else "HW"
        return f"<WiFiManager [{mode}] status={self._status.value}>"
