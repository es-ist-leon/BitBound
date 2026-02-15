"""Tests for CLI Tool."""

import pytest
from unittest.mock import patch
from bitbound.cli import create_parser, cmd_boards, cmd_info, cmd_scan


class TestCLIParser:
    def test_create_parser(self):
        parser = create_parser()
        assert parser is not None

    def test_version_flag(self):
        parser = create_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--version"])
        assert exc.value.code == 0

    def test_scan_command(self):
        parser = create_parser()
        args = parser.parse_args(["scan"])
        assert args.command == "scan"
        assert args.bus == "all"

    def test_scan_with_bus(self):
        parser = create_parser()
        args = parser.parse_args(["scan", "--bus", "i2c"])
        assert args.bus == "i2c"

    def test_init_command(self):
        parser = create_parser()
        args = parser.parse_args(["init", "myproject", "--board", "esp32"])
        assert args.command == "init"
        assert args.name == "myproject"
        assert args.board == "esp32"

    def test_init_default_name(self):
        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.name == "bitbound_project"

    def test_monitor_command(self):
        parser = create_parser()
        args = parser.parse_args(["monitor", "--device", "BME280", "--interval", "2.0"])
        assert args.command == "monitor"
        assert args.device == "BME280"
        assert args.interval == 2.0

    def test_config_set(self):
        parser = create_parser()
        args = parser.parse_args(["config", "set", "wifi.ssid", "MyNet"])
        assert args.command == "config"
        assert args.config_action == "set"
        assert args.key == "wifi.ssid"
        assert args.value == "MyNet"

    def test_deploy_command(self):
        parser = create_parser()
        args = parser.parse_args(["deploy", "--port", "COM3"])
        assert args.command == "deploy"
        assert args.port == "COM3"

    def test_boards_command(self):
        parser = create_parser()
        args = parser.parse_args(["boards"])
        assert args.command == "boards"


class TestCLICommands:
    def test_cmd_boards(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["boards"])
        cmd_boards(args)
        output = capsys.readouterr().out
        assert "esp32" in output
        assert "Raspberry Pi Pico" in output

    def test_cmd_info(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["info"])
        cmd_info(args)
        output = capsys.readouterr().out
        assert "Python" in output
        assert "BitBound" in output

    def test_cmd_scan(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["scan", "--bus", "i2c"])
        cmd_scan(args)
        output = capsys.readouterr().out
        assert "I2C" in output
