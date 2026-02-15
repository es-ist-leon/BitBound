"""Tests for MQTT Client."""

import pytest
from bitbound.network.mqtt import MQTTClient, MQTTConfig


class TestMQTTClient:
    def test_create_client(self):
        mqtt = MQTTClient(broker="localhost")
        assert not mqtt.is_connected

    def test_connect_simulation(self):
        mqtt = MQTTClient()
        result = mqtt.connect()
        assert result is True
        assert mqtt.is_connected

    def test_disconnect(self):
        mqtt = MQTTClient()
        mqtt.connect()
        mqtt.disconnect()
        assert not mqtt.is_connected

    def test_publish(self):
        mqtt = MQTTClient()
        mqtt.connect()
        result = mqtt.publish("test/topic", "hello")
        assert result is True

    def test_publish_dict(self):
        mqtt = MQTTClient()
        mqtt.connect()
        result = mqtt.publish("test/topic", {"temp": 23.5})
        assert result is True

    def test_publish_number(self):
        mqtt = MQTTClient()
        mqtt.connect()
        assert mqtt.publish("test/temp", 23.5) is True
        assert mqtt.publish("test/count", 42) is True

    def test_subscribe_and_receive(self):
        received = []
        mqtt = MQTTClient()
        mqtt.connect()
        mqtt.subscribe("test/#", lambda topic, msg: received.append((topic, msg)))
        mqtt.publish("test/data", "value")
        assert len(received) == 1
        assert received[0][0] == "test/data"

    def test_unsubscribe(self):
        mqtt = MQTTClient()
        mqtt.connect()
        mqtt.subscribe("test/topic", lambda t, m: None)
        mqtt.unsubscribe("test/topic")
        # Should not error

    def test_topic_matching(self):
        mqtt = MQTTClient()
        assert mqtt._topic_matches("sensors/#", "sensors/temp") is True
        assert mqtt._topic_matches("sensors/+", "sensors/temp") is True
        assert mqtt._topic_matches("sensors/temp", "sensors/humidity") is False

    def test_context_manager(self):
        with MQTTClient() as mqtt:
            assert mqtt.is_connected
        assert not mqtt.is_connected

    def test_config(self):
        config = MQTTConfig(broker="test.broker", port=1884, client_id="test")
        mqtt = MQTTClient(config=config)
        assert mqtt._config.broker == "test.broker"
        assert mqtt._config.port == 1884

    def test_repr(self):
        mqtt = MQTTClient(broker="test.local")
        assert "MQTTClient" in repr(mqtt)
        assert "test.local" in repr(mqtt)
