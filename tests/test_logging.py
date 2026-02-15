"""Tests for Data Logger."""

import os
import time
import tempfile
import pytest
from bitbound.logging.datalogger import DataLogger, LogFormat, LogEntry
from bitbound.logging.ringbuffer import RingBuffer
from bitbound.logging.storage import Storage, FileStorage


class TestLogEntry:
    def test_create_entry(self):
        entry = LogEntry(values={"temperature": 23.5, "humidity": 65})
        assert entry.values["temperature"] == 23.5
        assert entry.timestamp > 0

    def test_to_csv(self):
        entry = LogEntry(
            timestamp=1000.0,
            device_name="sensor1",
            values={"temp": 23.5, "hum": 65}
        )
        csv = entry.to_csv()
        assert "1000.0" in csv
        assert "sensor1" in csv

    def test_to_json(self):
        entry = LogEntry(values={"temp": 23.5})
        json_str = entry.to_json()
        assert "temp" in json_str
        assert "23.5" in json_str

    def test_to_dict(self):
        entry = LogEntry(device_name="test", values={"v": 1})
        d = entry.to_dict()
        assert d["device"] == "test"
        assert d["values"]["v"] == 1


class TestDataLogger:
    def test_create_logger(self):
        logger = DataLogger("test")
        assert logger.entry_count == 0
        assert not logger.is_running

    def test_log_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger("test", path=tmpdir, format=LogFormat.CSV)
            entry = logger.log({"temperature": 23.5}, device_name="sensor")
            assert logger.entry_count == 1
            assert entry.values["temperature"] == 23.5
            logger.close()

    def test_log_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger("test", path=tmpdir, format=LogFormat.JSONL)
            logger.log({"temp": 23.5})
            logger.log({"temp": 24.0})
            assert logger.entry_count == 2
            logger.close()

    def test_get_entries(self):
        logger = DataLogger("test")
        logger.log({"a": 1})
        logger.log({"b": 2})
        logger.log({"c": 3})
        entries = logger.get_entries(count=2)
        assert len(entries) == 2
        logger.close()

    def test_get_entries_by_device(self):
        logger = DataLogger("test")
        logger.log({"v": 1}, device_name="sensor1")
        logger.log({"v": 2}, device_name="sensor2")
        logger.log({"v": 3}, device_name="sensor1")
        entries = logger.get_entries(device_name="sensor1")
        assert len(entries) == 2
        logger.close()

    def test_clear_entries(self):
        logger = DataLogger("test")
        logger.log({"v": 1})
        logger.clear()
        assert logger.entry_count == 0
        logger.close()

    def test_on_entry_callback(self):
        logged = []
        logger = DataLogger("test")
        logger.on_entry(lambda e: logged.append(e))
        logger.log({"v": 1})
        assert len(logged) == 1
        logger.close()

    def test_context_manager(self):
        with DataLogger("test") as logger:
            logger.log({"v": 1})
            assert logger.entry_count == 1

    def test_repr(self):
        logger = DataLogger("mylog", format=LogFormat.JSON)
        assert "DataLogger" in repr(logger)
        assert "mylog" in repr(logger)


class TestRingBuffer:
    def test_create_buffer(self):
        buf = RingBuffer(capacity=10)
        assert buf.count == 0
        assert buf.capacity == 10
        assert not buf.is_full

    def test_append(self):
        buf = RingBuffer(capacity=5)
        buf.append({"temp": 23.5})
        assert buf.count == 1

    def test_overflow(self):
        buf = RingBuffer(capacity=3)
        buf.append({"v": 1})
        buf.append({"v": 2})
        buf.append({"v": 3})
        buf.append({"v": 4})  # Overwrites oldest
        assert buf.count == 3
        assert buf.is_full
        latest = buf.latest(1)
        assert latest[0].values["v"] == 4

    def test_latest(self):
        buf = RingBuffer(capacity=10)
        buf.append({"v": 1})
        buf.append({"v": 2})
        buf.append({"v": 3})
        latest = buf.latest(2)
        assert len(latest) == 2
        assert latest[0].values["v"] == 3
        assert latest[1].values["v"] == 2

    def test_oldest(self):
        buf = RingBuffer(capacity=10)
        buf.append({"v": 1})
        buf.append({"v": 2})
        buf.append({"v": 3})
        oldest = buf.oldest(2)
        assert len(oldest) == 2
        assert oldest[0].values["v"] == 1
        assert oldest[1].values["v"] == 2

    def test_all(self):
        buf = RingBuffer(capacity=5)
        for i in range(5):
            buf.append({"v": i})
        entries = buf.all()
        assert len(entries) == 5

    def test_average(self):
        buf = RingBuffer(capacity=10)
        buf.append({"temp": 20.0})
        buf.append({"temp": 25.0})
        buf.append({"temp": 30.0})
        avg = buf.average("temp")
        assert avg == 25.0

    def test_min_max(self):
        buf = RingBuffer(capacity=10)
        buf.append({"v": 10})
        buf.append({"v": 20})
        buf.append({"v": 5})
        assert buf.min_value("v") == 5
        assert buf.max_value("v") == 20

    def test_since(self):
        buf = RingBuffer(capacity=10)
        t = time.time()
        buf.append({"v": 1}, timestamp=t - 10)
        buf.append({"v": 2}, timestamp=t - 5)
        buf.append({"v": 3}, timestamp=t)
        entries = buf.since(t - 6)
        assert len(entries) == 2

    def test_clear(self):
        buf = RingBuffer(capacity=5)
        buf.append({"v": 1})
        buf.clear()
        assert buf.count == 0

    def test_len(self):
        buf = RingBuffer(capacity=10)
        buf.append({"v": 1})
        buf.append({"v": 2})
        assert len(buf) == 2

    def test_average_missing_key(self):
        buf = RingBuffer(capacity=5)
        buf.append({"v": 1})
        assert buf.average("nonexistent") is None

    def test_repr(self):
        buf = RingBuffer(capacity=100)
        assert "RingBuffer" in repr(buf)


class TestStorage:
    def test_create_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            assert storage is not None

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            storage.save("test.json", {"key": "value"})
            data = storage.load("test.json")
            assert data["key"] == "value"

    def test_load_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            data = storage.load("missing.json", default=42)
            assert data == 42

    def test_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            assert not storage.exists("test.json")
            storage.save("test.json", {"data": 1})
            assert storage.exists("test.json")

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            storage.save("test.json", {"data": 1})
            assert storage.delete("test.json") is True
            assert not storage.exists("test.json")

    def test_list_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            storage.save("a.json", 1)
            storage.save("b.json", 2)
            keys = storage.list_keys()
            assert len(keys) == 2

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(tmpdir)
            storage.save("a.json", 1)
            storage.save("b.json", 2)
            storage.clear()
            assert len(storage.list_keys()) == 0


class TestFileStorage:
    def test_write_and_read_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileStorage(tmpdir)
            fs.write_text("hello.txt", "Hello World")
            content = fs.read_text("hello.txt")
            assert content == "Hello World"

    def test_write_and_read_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileStorage(tmpdir)
            fs.write_bytes("data.bin", b"\x00\x01\x02")
            data = fs.read_bytes("data.bin")
            assert data == b"\x00\x01\x02"

    def test_append_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileStorage(tmpdir)
            fs.write_text("log.txt", "line1\n")
            fs.append_text("log.txt", "line2\n")
            content = fs.read_text("log.txt")
            assert "line1" in content
            assert "line2" in content

    def test_file_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileStorage(tmpdir)
            fs.write_text("test.txt", "12345")
            assert fs.file_size("test.txt") == 5

    def test_read_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fs = FileStorage(tmpdir)
            assert fs.read_text("missing.txt") is None
            assert fs.read_bytes("missing.bin") is None
