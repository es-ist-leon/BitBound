"""
Tests for BitBound units module.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bitbound.units import parse_value, Unit, convert


class TestParseValue:
    """Tests for parse_value function."""
    
    def test_parse_celsius(self):
        value, unit = parse_value("25°C")
        assert value == 25.0
        assert unit.unit_type == "temperature"
        assert unit.symbol == "°C"
    
    def test_parse_fahrenheit(self):
        value, unit = parse_value("77°F")
        assert value == 77.0
        assert unit.unit_type == "temperature"
    
    def test_parse_pressure_hpa(self):
        value, unit = parse_value("1013hPa")
        assert value == 1013.0
        assert unit.unit_type == "pressure"
    
    def test_parse_percentage(self):
        value, unit = parse_value("50%")
        assert value == 50.0
        assert unit.unit_type == "percentage"
    
    def test_parse_plain_number(self):
        value, unit = parse_value("42")
        assert value == 42.0
        assert unit is None
    
    def test_parse_negative(self):
        value, unit = parse_value("-10°C")
        assert value == -10.0
    
    def test_parse_decimal(self):
        value, unit = parse_value("23.5°C")
        assert value == 23.5
    
    def test_parse_voltage(self):
        value, unit = parse_value("3.3V")
        assert value == 3.3
        assert unit.unit_type == "voltage"
    
    def test_parse_milliamps(self):
        value, unit = parse_value("100mA")
        assert value == 100.0
        assert unit.unit_type == "current"


class TestUnitConversion:
    """Tests for unit conversion."""
    
    def test_celsius_to_kelvin(self):
        _, unit = parse_value("0°C")
        assert abs(unit.to_si() - 273.15) < 0.01
    
    def test_fahrenheit_to_kelvin(self):
        _, unit = parse_value("32°F")
        assert abs(unit.to_si() - 273.15) < 0.01
    
    def test_hpa_to_pa(self):
        _, unit = parse_value("1013hPa")
        assert unit.to_si() == 101300.0
    
    def test_millivolt_to_volt(self):
        _, unit = parse_value("3300mV")
        assert unit.to_si() == 3.3


class TestUnitComparison:
    """Tests for Unit comparison operators."""
    
    def test_unit_greater_than(self):
        _, u1 = parse_value("30°C")
        _, u2 = parse_value("25°C")
        assert u1 > u2
    
    def test_unit_less_than(self):
        _, u1 = parse_value("20°C")
        _, u2 = parse_value("25°C")
        assert u1 < u2
    
    def test_unit_equal(self):
        _, u1 = parse_value("25°C")
        _, u2 = parse_value("25°C")
        assert u1 == u2
    
    def test_compare_to_number(self):
        _, unit = parse_value("25°C")
        assert unit > 20
        assert unit < 30


class TestConvert:
    """Tests for convert function."""
    
    def test_convert_celsius_to_fahrenheit(self):
        result = convert(0, "°C", "°F")
        assert abs(result - 32) < 0.1
    
    def test_convert_hpa_to_mbar(self):
        result = convert(1013, "hPa", "mbar")
        assert abs(result - 1013) < 0.1
    
    def test_convert_mm_to_cm(self):
        result = convert(100, "mm", "cm")
        assert result == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
