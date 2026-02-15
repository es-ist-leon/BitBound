"""Tests for WebSocket Client."""

import pytest
from bitbound.network.websocket import WebSocketClient


class TestWebSocketClient:
    def _sim_ws(self, url="ws://localhost/ws"):
        """Create a WebSocketClient forced into simulation mode."""
        ws = WebSocketClient(url)
        return ws

    def _sim_connect(self, ws):
        """Force simulation connect."""
        ws._simulation = True
        ws._connected = True
        ws._fire_connect()
        return True

    def test_create_client(self):
        ws = WebSocketClient("ws://localhost/ws")
        assert not ws.is_connected

    def test_connect_simulation(self):
        ws = self._sim_ws()
        self._sim_connect(ws)
        assert ws.is_connected

    def test_disconnect(self):
        ws = self._sim_ws()
        self._sim_connect(ws)
        ws.disconnect()
        assert not ws.is_connected

    def test_send(self):
        ws = self._sim_ws()
        self._sim_connect(ws)
        result = ws.send("hello")
        assert result is True
        assert "hello" in ws._sim_outbox

    def test_send_dict(self):
        ws = self._sim_ws()
        self._sim_connect(ws)
        ws.send({"temperature": 23.5})
        assert len(ws._sim_outbox) == 1

    def test_message_callback(self):
        received = []
        ws = self._sim_ws()
        ws.on_message(lambda msg: received.append(msg))
        self._sim_connect(ws)
        ws.sim_receive("test message")
        assert len(received) == 1
        assert received[0] == "test message"

    def test_connect_callback(self):
        connected = []
        ws = self._sim_ws()
        ws.on_connect(lambda: connected.append(True))
        self._sim_connect(ws)
        assert len(connected) == 1

    def test_disconnect_callback(self):
        disconnected = []
        ws = self._sim_ws()
        ws.on_disconnect(lambda: disconnected.append(True))
        self._sim_connect(ws)
        ws.disconnect()
        assert len(disconnected) == 1

    def test_context_manager(self):
        with WebSocketClient("ws://localhost/ws") as ws:
            assert ws.is_connected
        assert not ws.is_connected

    def test_send_not_connected(self):
        ws = WebSocketClient("ws://localhost/ws")
        result = ws.send("hello")
        assert result is False

    def test_repr(self):
        ws = WebSocketClient("ws://test.local/ws")
        assert "WebSocketClient" in repr(ws)
        assert "test.local" in repr(ws)
