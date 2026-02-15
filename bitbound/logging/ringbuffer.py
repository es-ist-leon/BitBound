"""
Ring Buffer for BitBound.

Memory-efficient circular buffer for sensor data on
memory-constrained microcontrollers.
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BufferEntry:
    """A single ring buffer entry."""
    timestamp: float
    values: Dict[str, Any]

    def __repr__(self) -> str:
        return f"BufferEntry(t={self.timestamp:.1f}, {self.values})"


class RingBuffer:
    """
    Fixed-size circular buffer for sensor data.

    Automatically overwrites oldest entries when full.
    Ideal for memory-constrained microcontrollers.

    Example:
        from bitbound.logging import RingBuffer

        buf = RingBuffer(capacity=100)
        buf.append({"temperature": 23.5})
        buf.append({"temperature": 24.0})

        print(buf.latest())     # Most recent entry
        print(buf.average("temperature"))  # Average of all entries
    """

    def __init__(self, capacity: int = 100):
        """
        Initialize ring buffer.

        Args:
            capacity: Maximum number of entries
        """
        self._capacity = capacity
        self._buffer: List[Optional[BufferEntry]] = [None] * capacity
        self._head = 0
        self._count = 0

    def append(self, values: Dict[str, Any], timestamp: Optional[float] = None) -> None:
        """
        Add an entry to the buffer.

        Args:
            values: Key-value pairs to store
            timestamp: Optional timestamp (default: now)
        """
        entry = BufferEntry(
            timestamp=timestamp or time.time(),
            values=values,
        )
        self._buffer[self._head] = entry
        self._head = (self._head + 1) % self._capacity
        if self._count < self._capacity:
            self._count += 1

    def latest(self, count: int = 1) -> List[BufferEntry]:
        """
        Get the most recent entries.

        Args:
            count: Number of entries to return

        Returns:
            List of most recent entries (newest first)
        """
        if self._count == 0:
            return []

        count = min(count, self._count)
        result = []
        idx = (self._head - 1) % self._capacity
        for _ in range(count):
            entry = self._buffer[idx]
            if entry is not None:
                result.append(entry)
            idx = (idx - 1) % self._capacity
        return result

    def oldest(self, count: int = 1) -> List[BufferEntry]:
        """
        Get the oldest entries.

        Args:
            count: Number of entries to return

        Returns:
            List of oldest entries (oldest first)
        """
        if self._count == 0:
            return []

        count = min(count, self._count)
        result = []

        if self._count < self._capacity:
            start = 0
        else:
            start = self._head

        idx = start
        for _ in range(count):
            entry = self._buffer[idx]
            if entry is not None:
                result.append(entry)
            idx = (idx + 1) % self._capacity
        return result

    def all(self) -> List[BufferEntry]:
        """
        Get all entries in chronological order.

        Returns:
            List of all entries
        """
        if self._count == 0:
            return []

        if self._count < self._capacity:
            return [e for e in self._buffer[:self._count] if e is not None]

        result = []
        idx = self._head
        for _ in range(self._capacity):
            entry = self._buffer[idx]
            if entry is not None:
                result.append(entry)
            idx = (idx + 1) % self._capacity
        return result

    def average(self, key: str) -> Optional[float]:
        """
        Calculate the average of a specific value across all entries.

        Args:
            key: The value key to average

        Returns:
            Average value or None
        """
        values = []
        for entry in self.all():
            val = entry.values.get(key)
            if val is not None and isinstance(val, (int, float)):
                values.append(val)

        if not values:
            return None
        return sum(values) / len(values)

    def min_value(self, key: str) -> Optional[float]:
        """Get the minimum value for a key."""
        values = [e.values.get(key) for e in self.all()
                  if key in e.values and isinstance(e.values[key], (int, float))]
        return min(values) if values else None

    def max_value(self, key: str) -> Optional[float]:
        """Get the maximum value for a key."""
        values = [e.values.get(key) for e in self.all()
                  if key in e.values and isinstance(e.values[key], (int, float))]
        return max(values) if values else None

    def since(self, timestamp: float) -> List[BufferEntry]:
        """Get entries since a specific timestamp."""
        return [e for e in self.all() if e.timestamp >= timestamp]

    def clear(self) -> None:
        """Clear all entries."""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._count = 0

    @property
    def count(self) -> int:
        """Number of entries in buffer."""
        return self._count

    @property
    def capacity(self) -> int:
        """Maximum capacity."""
        return self._capacity

    @property
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self._count >= self._capacity

    def __len__(self) -> int:
        return self._count

    def __repr__(self) -> str:
        return f"<RingBuffer {self._count}/{self._capacity}>"
