"""
WebSocket Client for BitBound.

Provides WebSocket connectivity for real-time communication.
"""

import threading
import time
import json
from typing import Any, Callable, Dict, List, Optional


class WebSocketClient:
    """
    Simple WebSocket client for MicroPython and desktop.

    Example:
        from bitbound.network import WebSocketClient

        ws = WebSocketClient("ws://server.local/ws")
        ws.on_message(lambda msg: print(f"Received: {msg}"))
        ws.connect()
        ws.send({"temperature": 23.5})
    """

    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        self._url = url
        self._headers = headers or {}
        self._ws = None
        self._simulation = True
        self._connected = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._message_callbacks: List[Callable] = []
        self._connect_callbacks: List[Callable] = []
        self._disconnect_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []
        self._sim_inbox: List[Any] = []
        self._sim_outbox: List[Any] = []

    def connect(self) -> bool:
        """
        Connect to the WebSocket server.

        Returns:
            True if connected
        """
        try:
            # Try MicroPython
            try:
                import uwebsocket
                self._ws = uwebsocket.connect(self._url)
                self._simulation = False
                self._connected = True
                self._start_receiver()
                self._fire_connect()
                return True
            except ImportError:
                pass

            # Try websocket-client (desktop)
            try:
                import websocket
                self._ws = websocket.WebSocketApp(
                    self._url,
                    header=self._headers,
                    on_message=self._on_ws_message,
                    on_error=self._on_ws_error,
                    on_close=self._on_ws_close,
                    on_open=self._on_ws_open,
                )
                self._thread = threading.Thread(target=self._ws.run_forever, daemon=True)
                self._thread.start()
                self._simulation = False
                # wait briefly for connection
                time.sleep(0.5)
                self._connected = True
                return True
            except ImportError:
                pass

            # Simulation mode
            self._simulation = True
            self._connected = True
            self._fire_connect()
            return True

        except Exception as e:
            self._fire_error(e)
            return False

    def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        self._running = False
        self._connected = False

        if self._ws:
            try:
                if hasattr(self._ws, "close"):
                    self._ws.close()
            except Exception:
                pass
        self._ws = None
        self._fire_disconnect()

    def send(self, data: Any) -> bool:
        """
        Send data through the WebSocket.

        Args:
            data: Data to send (str, bytes, dict, list)

        Returns:
            True if sent
        """
        if not self._connected:
            return False

        if isinstance(data, (dict, list)):
            data = json.dumps(data)

        if self._simulation:
            self._sim_outbox.append(data)
            return True

        try:
            if hasattr(self._ws, "send"):
                self._ws.send(data if isinstance(data, str) else data.decode("utf-8"))
            elif hasattr(self._ws, "write"):
                payload = data.encode("utf-8") if isinstance(data, str) else data
                self._ws.write(payload)
            return True
        except Exception as e:
            self._fire_error(e)
            return False

    def on_message(self, callback: Callable[[Any], None]) -> None:
        """Register a message callback."""
        self._message_callbacks.append(callback)

    def on_connect(self, callback: Callable[[], None]) -> None:
        """Register a connect callback."""
        self._connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable[[], None]) -> None:
        """Register a disconnect callback."""
        self._disconnect_callbacks.append(callback)

    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register an error callback."""
        self._error_callbacks.append(callback)

    def sim_receive(self, data: Any) -> None:
        """Simulate receiving a message (for testing)."""
        self._sim_inbox.append(data)
        self._fire_message(data)

    def _start_receiver(self) -> None:
        """Start the message receiver thread (MicroPython)."""
        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()

    def _receive_loop(self) -> None:
        """Receive loop for MicroPython WebSocket."""
        while self._running:
            try:
                if hasattr(self._ws, "read"):
                    data = self._ws.read()
                    if data:
                        self._fire_message(data.decode("utf-8") if isinstance(data, bytes) else data)
            except Exception as e:
                self._fire_error(e)
                break
            time.sleep(0.01)

    def _on_ws_message(self, ws, message) -> None:
        """Websocket-client message callback."""
        self._fire_message(message)

    def _on_ws_error(self, ws, error) -> None:
        """Websocket-client error callback."""
        self._fire_error(error)

    def _on_ws_close(self, ws, close_status_code, close_msg) -> None:
        """Websocket-client close callback."""
        self._connected = False
        self._fire_disconnect()

    def _on_ws_open(self, ws) -> None:
        """Websocket-client open callback."""
        self._connected = True
        self._fire_connect()

    def _fire_message(self, data: Any) -> None:
        for cb in self._message_callbacks:
            try:
                cb(data)
            except Exception as e:
                print(f"WebSocket message callback error: {e}")

    def _fire_connect(self) -> None:
        for cb in self._connect_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"WebSocket connect callback error: {e}")

    def _fire_disconnect(self) -> None:
        for cb in self._disconnect_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"WebSocket disconnect callback error: {e}")

    def _fire_error(self, error: Any) -> None:
        for cb in self._error_callbacks:
            try:
                cb(error)
            except Exception as e:
                print(f"WebSocket error callback error: {e}")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        mode = "SIM" if self._simulation else "HW"
        status = "connected" if self._connected else "disconnected"
        return f"<WebSocketClient [{mode}] {self._url} [{status}]>"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
