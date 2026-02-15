"""
Data Logger for BitBound.

Logs sensor data to files in CSV, JSON, or binary format.
"""

import time
import json
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class LogFormat(Enum):
    """Supported log file formats."""
    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    BINARY = "binary"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: float = field(default_factory=time.time)
    device_name: str = ""
    values: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    def to_csv(self, separator: str = ",") -> str:
        """Convert to CSV line."""
        parts = [str(self.timestamp), self.device_name]
        parts.extend(str(v) for v in self.values.values())
        return separator.join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "device": self.device_name,
            "values": self.values,
            "tags": self.tags,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class DataLogger:
    """
    High-level data logger for sensor data.

    Example:
        from bitbound.logging import DataLogger

        logger = DataLogger("sensor_data", format=LogFormat.CSV)
        logger.start(interval_ms=5000)

        # Add devices to log
        logger.add_device(sensor, properties=["temperature", "humidity"])

        # Or log manually
        logger.log({"temperature": 23.5, "humidity": 65.0})
    """

    def __init__(
        self,
        name: str = "data",
        format: LogFormat = LogFormat.CSV,
        path: str = ".",
        max_entries: int = 0,
        max_file_size: int = 0,
        rotate: bool = False,
        max_files: int = 5,
        flush_interval: int = 10,
    ):
        """
        Initialize data logger.

        Args:
            name: Log file base name
            format: Output format
            path: Directory for log files
            max_entries: Max entries per file (0 = unlimited)
            max_file_size: Max file size in bytes (0 = unlimited)
            rotate: Enable log rotation
            max_files: Max number of rotated files
            flush_interval: Flush to disk every N entries
        """
        self._name = name
        self._format = format
        self._path = path
        self._max_entries = max_entries
        self._max_file_size = max_file_size
        self._rotate = rotate
        self._max_files = max_files
        self._flush_interval = flush_interval

        self._entries: List[LogEntry] = []
        self._entry_count = 0
        self._file = None
        self._file_index = 0
        self._devices: List[Dict[str, Any]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[LogEntry], None]] = []
        self._header_written = False

    def _get_filename(self) -> str:
        """Get the current log filename."""
        ext_map = {
            LogFormat.CSV: ".csv",
            LogFormat.JSON: ".json",
            LogFormat.JSONL: ".jsonl",
            LogFormat.BINARY: ".bin",
        }
        ext = ext_map.get(self._format, ".log")
        if self._rotate and self._file_index > 0:
            return f"{self._path}/{self._name}_{self._file_index}{ext}"
        return f"{self._path}/{self._name}{ext}"

    def _open_file(self) -> None:
        """Open or create the log file."""
        if self._file:
            self._file.close()

        filename = self._get_filename()
        mode = "a"
        try:
            self._file = open(filename, mode)
            if self._format == LogFormat.CSV and not self._header_written:
                # CSV header will be written on first log
                pass
        except Exception as e:
            print(f"Cannot open log file {filename}: {e}")
            self._file = None

    def _rotate_file(self) -> None:
        """Rotate log files."""
        if self._file:
            self._file.close()
            self._file = None

        self._file_index += 1
        if self._file_index >= self._max_files:
            self._file_index = 0

        self._entry_count = 0
        self._header_written = False
        self._open_file()

    def add_device(
        self,
        device: Any,
        properties: Optional[List[str]] = None,
        name: Optional[str] = None
    ) -> None:
        """
        Add a device to be logged.

        Args:
            device: Device to log
            properties: List of properties to log (None = all)
            name: Override device name
        """
        self._devices.append({
            "device": device,
            "properties": properties,
            "name": name or getattr(device, "name", str(device)),
        })

    def log(
        self,
        values: Dict[str, Any],
        device_name: str = "",
        tags: Optional[Dict[str, str]] = None
    ) -> LogEntry:
        """
        Log a data entry manually.

        Args:
            values: Key-value pairs to log
            device_name: Name of the source device
            tags: Additional metadata tags

        Returns:
            The created LogEntry
        """
        entry = LogEntry(
            timestamp=time.time(),
            device_name=device_name,
            values=values,
            tags=tags or {},
        )

        with self._lock:
            self._entries.append(entry)
            self._entry_count += 1

            # Write to file
            self._write_entry(entry)

            # Check rotation
            if self._rotate and self._max_entries > 0:
                if self._entry_count >= self._max_entries:
                    self._rotate_file()

        # Fire callbacks
        for cb in self._callbacks:
            try:
                cb(entry)
            except Exception as e:
                print(f"Logger callback error: {e}")

        return entry

    def _write_entry(self, entry: LogEntry) -> None:
        """Write an entry to the log file."""
        if self._file is None:
            self._open_file()
        if self._file is None:
            return

        try:
            if self._format == LogFormat.CSV:
                if not self._header_written:
                    header = "timestamp,device," + ",".join(entry.values.keys())
                    self._file.write(header + "\n")
                    self._header_written = True
                self._file.write(entry.to_csv() + "\n")

            elif self._format == LogFormat.JSON:
                # For JSON format, we accumulate in memory
                pass

            elif self._format == LogFormat.JSONL:
                self._file.write(entry.to_json() + "\n")

            # Periodic flush
            if self._entry_count % self._flush_interval == 0:
                self._file.flush()

        except Exception as e:
            print(f"Log write error: {e}")

    def _log_devices(self) -> None:
        """Log all registered devices."""
        for dev_info in self._devices:
            device = dev_info["device"]
            properties = dev_info["properties"]
            name = dev_info["name"]

            try:
                if properties:
                    values = {p: getattr(device, p, None) for p in properties}
                elif hasattr(device, "read_all"):
                    values = device.read_all()
                else:
                    continue

                self.log(values, device_name=name)
            except Exception as e:
                print(f"Device log error ({name}): {e}")

    def start(self, interval_ms: int = 1000) -> None:
        """
        Start automatic logging at regular intervals.

        Args:
            interval_ms: Logging interval in milliseconds
        """
        if self._running:
            return

        self._running = True
        interval = interval_ms / 1000.0

        def _log_loop():
            while self._running:
                self._log_devices()
                time.sleep(interval)

        self._thread = threading.Thread(target=_log_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop automatic logging."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self.flush()

    def flush(self) -> None:
        """Flush all buffered data to disk."""
        with self._lock:
            if self._format == LogFormat.JSON and self._entries:
                if self._file is None:
                    self._open_file()
                if self._file:
                    data = [e.to_dict() for e in self._entries]
                    self._file.seek(0)
                    self._file.write(json.dumps(data, indent=2))
                    self._file.flush()

            elif self._file:
                self._file.flush()

    def get_entries(
        self,
        count: int = 0,
        since: Optional[float] = None,
        device_name: Optional[str] = None
    ) -> List[LogEntry]:
        """
        Get logged entries from memory.

        Args:
            count: Max entries to return (0 = all)
            since: Only entries after this timestamp
            device_name: Filter by device name

        Returns:
            List of LogEntry objects
        """
        with self._lock:
            entries = list(self._entries)

        if since:
            entries = [e for e in entries if e.timestamp >= since]
        if device_name:
            entries = [e for e in entries if e.device_name == device_name]
        if count > 0:
            entries = entries[-count:]

        return entries

    def clear(self) -> None:
        """Clear in-memory entries."""
        with self._lock:
            self._entries.clear()
            self._entry_count = 0

    def on_entry(self, callback: Callable[[LogEntry], None]) -> None:
        """Register a callback for each log entry."""
        self._callbacks.append(callback)

    @property
    def entry_count(self) -> int:
        """Total entries logged."""
        return self._entry_count

    @property
    def is_running(self) -> bool:
        return self._running

    def close(self) -> None:
        """Stop logging and close files."""
        self.stop()
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self) -> str:
        return f"<DataLogger {self._name} format={self._format.value} entries={self._entry_count}>"
