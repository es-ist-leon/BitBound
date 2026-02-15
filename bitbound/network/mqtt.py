"""
MQTT Client for BitBound.

Provides a simple MQTT publish/subscribe interface for IoT communication.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class MQTTConfig:
    """MQTT connection configuration."""
    broker: str = "localhost"
    port: int = 1883
    client_id: str = "bitbound"
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    ssl: bool = False
    ssl_params: Dict[str, Any] = field(default_factory=dict)
    clean_session: bool = True
    qos: int = 0
    retain: bool = False
    last_will: Optional[Dict[str, Any]] = None


class MQTTClient:
    """
    High-level MQTT client.

    Example:
        from bitbound.network import MQTTClient

        mqtt = MQTTClient(broker="broker.hivemq.com")
        mqtt.connect()

        mqtt.subscribe("sensors/#", lambda topic, msg: print(f"{topic}: {msg}"))
        mqtt.publish("sensors/temperature", "23.5")
    """

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        client_id: str = "bitbound",
        config: Optional[MQTTConfig] = None,
        **kwargs
    ):
        if config:
            self._config = config
        else:
            self._config = MQTTConfig(
                broker=broker, port=port, client_id=client_id, **kwargs
            )

        self._client = None
        self._simulation = True
        self._connected = False
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._message_queue: List[Tuple[str, bytes]] = []
        self._lock = threading.Lock()
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False

    def connect(self) -> bool:
        """
        Connect to the MQTT broker.

        Returns:
            True if connected
        """
        try:
            # Try MicroPython umqtt
            try:
                from umqtt.simple import MQTTClient as uMQTT
                self._client = uMQTT(
                    self._config.client_id,
                    self._config.broker,
                    port=self._config.port,
                    user=self._config.username,
                    password=self._config.password,
                    keepalive=self._config.keepalive,
                    ssl=self._config.ssl,
                    ssl_params=self._config.ssl_params if self._config.ssl else None,
                )

                if self._config.last_will:
                    self._client.set_last_will(
                        self._config.last_will.get("topic", ""),
                        self._config.last_will.get("message", ""),
                        self._config.last_will.get("retain", False),
                        self._config.last_will.get("qos", 0),
                    )

                self._client.set_callback(self._on_message)
                self._client.connect(clean_session=self._config.clean_session)
                self._simulation = False
                self._connected = True

                # Re-subscribe
                for topic in self._subscriptions:
                    self._client.subscribe(topic.encode(), self._config.qos)

                return True
            except ImportError:
                pass

            # Try paho-mqtt (desktop)
            try:
                import paho.mqtt.client as paho
                self._client = paho.Client(
                    client_id=self._config.client_id,
                    clean_session=self._config.clean_session,
                )
                if self._config.username:
                    self._client.username_pw_set(
                        self._config.username, self._config.password
                    )
                if self._config.last_will:
                    self._client.will_set(
                        self._config.last_will.get("topic", ""),
                        self._config.last_will.get("message", ""),
                        self._config.last_will.get("qos", 0),
                        self._config.last_will.get("retain", False),
                    )
                self._client.on_message = self._on_paho_message
                self._client.on_connect = self._on_paho_connect
                self._client.connect(self._config.broker, self._config.port, self._config.keepalive)
                self._client.loop_start()
                self._simulation = False
                self._connected = True
                return True
            except ImportError:
                pass

            # Simulation mode
            self._simulation = True
            self._connected = True
            return True

        except Exception as e:
            print(f"MQTT connect error: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self._running = False
        self._connected = False

        if self._client:
            try:
                if hasattr(self._client, "loop_stop"):
                    self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
        self._client = None

    def publish(
        self,
        topic: str,
        message: Any,
        qos: Optional[int] = None,
        retain: Optional[bool] = None
    ) -> bool:
        """
        Publish a message.

        Args:
            topic: MQTT topic
            message: Message payload (str, bytes, int, float)
            qos: Quality of Service (0, 1, 2)
            retain: Retain message on broker

        Returns:
            True if published
        """
        qos = qos if qos is not None else self._config.qos
        retain = retain if retain is not None else self._config.retain

        if isinstance(message, (int, float)):
            message = str(message)
        if isinstance(message, str):
            message = message.encode("utf-8")

        if self._simulation:
            with self._lock:
                self._message_queue.append((topic, message))
            # Deliver to local subscribers
            self._deliver_local(topic, message)
            return True

        try:
            if hasattr(self._client, "publish"):
                result = self._client.publish(topic, message, qos=qos, retain=retain)
                if hasattr(result, "rc"):
                    return result.rc == 0
                return True
        except Exception as e:
            print(f"MQTT publish error: {e}")
            return False

        return False

    def subscribe(
        self,
        topic: str,
        callback: Callable[[str, bytes], None],
        qos: Optional[int] = None
    ) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: MQTT topic (supports wildcards: +, #)
            callback: Function called with (topic, message)
            qos: Quality of Service
        """
        qos = qos if qos is not None else self._config.qos

        with self._lock:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            self._subscriptions[topic].append(callback)

        if not self._simulation and self._client and self._connected:
            try:
                if hasattr(self._client, "subscribe"):
                    self._client.subscribe(topic if isinstance(topic, str) else topic, qos)
            except Exception as e:
                print(f"MQTT subscribe error: {e}")

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        with self._lock:
            self._subscriptions.pop(topic, None)

        if not self._simulation and self._client:
            try:
                self._client.unsubscribe(topic)
            except Exception:
                pass

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if a topic matches a subscription pattern."""
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")

        i = 0
        for i, p in enumerate(pattern_parts):
            if p == "#":
                return True
            if i >= len(topic_parts):
                return False
            if p != "+" and p != topic_parts[i]:
                return False

        return i + 1 == len(topic_parts)

    def _deliver_local(self, topic: str, message: bytes) -> None:
        """Deliver message to matching local subscribers."""
        with self._lock:
            subs = dict(self._subscriptions)

        for pattern, callbacks in subs.items():
            if self._topic_matches(pattern, topic):
                for cb in callbacks:
                    try:
                        cb(topic, message)
                    except Exception as e:
                        print(f"MQTT callback error: {e}")

    def _on_message(self, topic: bytes, message: bytes) -> None:
        """MicroPython umqtt callback."""
        topic_str = topic.decode("utf-8") if isinstance(topic, bytes) else topic
        self._deliver_local(topic_str, message)

    def _on_paho_message(self, client, userdata, msg) -> None:
        """Paho MQTT callback."""
        self._deliver_local(msg.topic, msg.payload)

    def _on_paho_connect(self, client, userdata, flags, rc) -> None:
        """Paho MQTT connect callback - resubscribe on reconnect."""
        if rc == 0:
            self._connected = True
            with self._lock:
                for topic in self._subscriptions:
                    client.subscribe(topic, self._config.qos)

    def check_msg(self) -> None:
        """Check for pending messages (MicroPython polling mode)."""
        if not self._simulation and self._client and hasattr(self._client, "check_msg"):
            self._client.check_msg()

    @property
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected

    @property
    def messages(self) -> List[Tuple[str, bytes]]:
        """Get queued messages (simulation mode)."""
        with self._lock:
            msgs = list(self._message_queue)
            self._message_queue.clear()
            return msgs

    def __repr__(self) -> str:
        mode = "SIM" if self._simulation else "HW"
        return f"<MQTTClient [{mode}] {self._config.broker}:{self._config.port}>"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
