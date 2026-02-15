"""Tests for Async Support."""

import pytest
import asyncio
from bitbound.async_support import AsyncEventLoop, AsyncDevice, gather_readings, HAS_ASYNCIO


# Skip all tests if asyncio not available
pytestmark = pytest.mark.skipif(not HAS_ASYNCIO, reason="asyncio not available")


class MockDevice:
    """Mock device for async testing."""
    def __init__(self):
        self._temperature = 23.5
        self._humidity = 65.0
        self._properties = {"temperature", "humidity"}

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity

    @property
    def properties(self):
        return self._properties

    def read_all(self):
        return {"temperature": self._temperature, "humidity": self._humidity}


class TestAsyncEventLoop:
    def test_create_loop(self):
        loop = AsyncEventLoop()
        assert loop is not None

    @pytest.mark.asyncio
    async def test_read_async(self):
        loop = AsyncEventLoop()
        device = MockDevice()
        value = await loop.read_async(device, "temperature")
        assert value == 23.5

    @pytest.mark.asyncio
    async def test_read_all_async(self):
        loop = AsyncEventLoop()
        device = MockDevice()
        values = await loop.read_all_async(device)
        assert values["temperature"] == 23.5
        assert values["humidity"] == 65.0

    @pytest.mark.asyncio
    async def test_wait_for_threshold(self):
        loop = AsyncEventLoop()
        device = MockDevice()
        device._temperature = 30.0
        values = await loop.wait_for_threshold(device, "temperature > 25°C")
        assert values["temperature"] == 30.0

    @pytest.mark.asyncio
    async def test_wait_for_change(self):
        loop = AsyncEventLoop()
        device = MockDevice()

        async def change_value():
            await asyncio.sleep(0.05)
            device._temperature = 25.0

        asyncio.ensure_future(change_value())
        result = await loop.wait_for_change(device, "temperature", poll_interval=0.01, timeout=1.0)
        assert result == 25.0

    @pytest.mark.asyncio
    async def test_wait_for_change_timeout(self):
        loop = AsyncEventLoop()
        device = MockDevice()
        with pytest.raises(TimeoutError):
            await loop.wait_for_change(device, "temperature", poll_interval=0.01, timeout=0.05)

    @pytest.mark.asyncio
    async def test_periodic(self):
        loop = AsyncEventLoop()
        values = []
        await loop.periodic(lambda: values.append(1), interval=0.01, count=3)
        assert len(values) == 3


class TestAsyncDevice:
    @pytest.mark.asyncio
    async def test_read_all(self):
        device = MockDevice()
        async_dev = AsyncDevice(device)
        values = await async_dev.read_all()
        assert values["temperature"] == 23.5

    @pytest.mark.asyncio
    async def test_property_access(self):
        device = MockDevice()
        async_dev = AsyncDevice(device)
        temp = await async_dev.temperature
        assert temp == 23.5

    def test_repr(self):
        device = MockDevice()
        async_dev = AsyncDevice(device)
        assert "AsyncDevice" in repr(async_dev)


class TestGatherReadings:
    @pytest.mark.asyncio
    async def test_gather_multiple(self):
        d1 = MockDevice()
        d1._temperature = 20.0
        d2 = MockDevice()
        d2._temperature = 25.0

        results = await gather_readings(d1, d2)
        assert len(results) == 2
        assert results[0]["temperature"] == 20.0
        assert results[1]["temperature"] == 25.0

    @pytest.mark.asyncio
    async def test_gather_with_properties(self):
        d = MockDevice()
        results = await gather_readings(d, properties=["temperature"])
        assert "temperature" in results[0]
        assert "humidity" not in results[0]
