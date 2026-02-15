"""
Async support for BitBound.

Provides asyncio-compatible wrappers for hardware interaction,
enabling async/await patterns for MicroPython's uasyncio and
CPython's asyncio.
"""

import time
import threading
from typing import Any, Callable, Dict, List, Optional


# Try to import asyncio (works on both MicroPython uasyncio and CPython)
try:
    import asyncio
    HAS_ASYNCIO = True
except ImportError:
    try:
        import uasyncio as asyncio
        HAS_ASYNCIO = True
    except ImportError:
        HAS_ASYNCIO = False


class AsyncEventLoop:
    """
    Async event loop for BitBound.

    Provides an asyncio-based alternative to the polling EventLoop.

    Example:
        from bitbound.async_support import AsyncEventLoop

        loop = AsyncEventLoop()

        async def monitor_temp(sensor):
            while True:
                temp = await loop.read_async(sensor, "temperature")
                if temp > 30:
                    print("Too hot!")
                await asyncio.sleep(1)

        loop.run(monitor_temp(sensor))
    """

    def __init__(self):
        if not HAS_ASYNCIO:
            raise RuntimeError("asyncio/uasyncio not available")

        self._tasks: List[Any] = []
        self._running = False

    async def read_async(self, device: Any, property_name: str) -> Any:
        """
        Read a device property asynchronously.

        Args:
            device: Device to read from
            property_name: Property name to read

        Returns:
            Property value
        """
        # Yield to event loop, then read
        await asyncio.sleep(0)
        return getattr(device, property_name, None)

    async def read_all_async(self, device: Any) -> Dict[str, Any]:
        """Read all properties from a device asynchronously."""
        await asyncio.sleep(0)
        if hasattr(device, "read_all"):
            return device.read_all()
        return {}

    async def wait_for_threshold(
        self,
        device: Any,
        expression_str: str,
        poll_interval: float = 0.1
    ) -> Dict[str, Any]:
        """
        Wait until a threshold condition is met.

        Args:
            device: Device to monitor
            expression_str: Condition string (e.g., "temperature > 25°C")
            poll_interval: Poll interval in seconds

        Returns:
            Device values when condition became true
        """
        from .expression import parse_expression
        expr = parse_expression(expression_str)

        while True:
            values = await self.read_all_async(device)
            if expr.evaluate(values):
                return values
            await asyncio.sleep(poll_interval)

    async def wait_for_change(
        self,
        device: Any,
        property_name: str,
        poll_interval: float = 0.1,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Wait until a property value changes.

        Args:
            device: Device to monitor
            property_name: Property to watch
            poll_interval: Poll interval in seconds
            timeout: Max wait time (None = forever)

        Returns:
            New property value
        """
        initial = getattr(device, property_name, None)
        start = time.time()

        while True:
            current = getattr(device, property_name, None)
            if current != initial:
                return current

            if timeout and (time.time() - start) > timeout:
                raise TimeoutError(
                    f"Property '{property_name}' did not change within {timeout}s"
                )

            await asyncio.sleep(poll_interval)

    async def periodic(
        self,
        callback: Callable,
        interval: float,
        count: int = 0
    ) -> None:
        """
        Execute a callback periodically.

        Args:
            callback: Async or sync function to call
            interval: Interval in seconds
            count: Number of times to execute (0 = forever)
        """
        iterations = 0
        while count == 0 or iterations < count:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
            iterations += 1
            await asyncio.sleep(interval)

    def create_task(self, coro) -> Any:
        """Create an asyncio task."""
        task = asyncio.ensure_future(coro)
        self._tasks.append(task)
        return task

    def run(self, *coros) -> None:
        """
        Run coroutines in the asyncio event loop.

        Args:
            *coros: Coroutines to run
        """
        self._running = True

        async def _main():
            tasks = [asyncio.ensure_future(c) for c in coros]
            self._tasks.extend(tasks)
            await asyncio.gather(*tasks)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_main())
            else:
                loop.run_until_complete(_main())
        except RuntimeError:
            asyncio.run(_main())

    def stop(self) -> None:
        """Stop all running tasks."""
        self._running = False
        for task in self._tasks:
            if hasattr(task, "cancel"):
                task.cancel()
        self._tasks.clear()


class AsyncDevice:
    """
    Async wrapper for any BitBound device.

    Example:
        from bitbound.async_support import AsyncDevice

        async_sensor = AsyncDevice(sensor)
        temp = await async_sensor.temperature
        data = await async_sensor.read_all()
    """

    def __init__(self, device: Any):
        self._device = device

    async def read_all(self) -> Dict[str, Any]:
        """Read all properties asynchronously."""
        await asyncio.sleep(0)
        if hasattr(self._device, "read_all"):
            return self._device.read_all()
        return {}

    def __getattr__(self, name: str):
        """Proxy attribute access to create async getters."""
        attr = getattr(self._device, name, None)
        if attr is None:
            raise AttributeError(f"{name} not found on {self._device}")

        if callable(attr):
            async def async_method(*args, **kwargs):
                await asyncio.sleep(0)
                return attr(*args, **kwargs)
            return async_method

        # For properties, return a coroutine
        async def async_prop():
            await asyncio.sleep(0)
            return attr

        return async_prop()

    def __repr__(self) -> str:
        return f"<AsyncDevice wrapping {self._device}>"


async def gather_readings(*devices, properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Read from multiple devices concurrently.

    Args:
        *devices: Devices to read from
        properties: Specific properties to read (None = all)

    Returns:
        List of reading dictionaries
    """
    async def _read_one(device):
        await asyncio.sleep(0)
        if properties:
            return {p: getattr(device, p, None) for p in properties}
        elif hasattr(device, "read_all"):
            return device.read_all()
        return {}

    return await asyncio.gather(*[_read_one(d) for d in devices])
