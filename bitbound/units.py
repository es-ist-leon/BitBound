"""
Unit parsing and conversion for natural expressions.

Supports parsing expressions like "25°C", "1000hPa", "50%", etc.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Callable


@dataclass
class Unit:
    """Represents a physical unit with value and type."""
    value: float
    unit_type: str
    symbol: str
    
    def to_si(self) -> float:
        """Convert to SI base unit."""
        return UNIT_CONVERTERS.get(self.symbol, lambda x: x)(self.value)
    
    def __repr__(self) -> str:
        return f"{self.value}{self.symbol}"
    
    def __eq__(self, other):
        if isinstance(other, Unit):
            return self.to_si() == other.to_si() and self.unit_type == other.unit_type
        return self.value == other
    
    def __lt__(self, other):
        if isinstance(other, Unit):
            return self.to_si() < other.to_si()
        return self.value < other
    
    def __gt__(self, other):
        if isinstance(other, Unit):
            return self.to_si() > other.to_si()
        return self.value > other
    
    def __le__(self, other):
        return self == other or self < other
    
    def __ge__(self, other):
        return self == other or self > other


# Unit symbols and their types
UNIT_SYMBOLS: Dict[str, str] = {
    # Temperature
    "°C": "temperature",
    "°F": "temperature", 
    "K": "temperature",
    "C": "temperature",
    "F": "temperature",
    
    # Pressure
    "hPa": "pressure",
    "Pa": "pressure",
    "kPa": "pressure",
    "bar": "pressure",
    "mbar": "pressure",
    "psi": "pressure",
    "atm": "pressure",
    
    # Humidity / Percentage
    "%": "percentage",
    "RH": "humidity",
    "%RH": "humidity",
    
    # Length
    "mm": "length",
    "cm": "length",
    "m": "length",
    "km": "length",
    "in": "length",
    "ft": "length",
    
    # Time
    "ms": "time",
    "s": "time",
    "min": "time",
    "h": "time",
    
    # Electrical
    "V": "voltage",
    "mV": "voltage",
    "A": "current",
    "mA": "current",
    "µA": "current",
    "W": "power",
    "mW": "power",
    "kW": "power",
    "Ω": "resistance",
    "kΩ": "resistance",
    "MΩ": "resistance",
    
    # Light
    "lux": "illuminance",
    "lx": "illuminance",
    
    # Speed
    "rpm": "angular_velocity",
    "m/s": "velocity",
    "km/h": "velocity",
    
    # Frequency
    "Hz": "frequency",
    "kHz": "frequency",
    "MHz": "frequency",
}

# Conversion functions to SI base units
UNIT_CONVERTERS: Dict[str, Callable[[float], float]] = {
    # Temperature -> Kelvin
    "°C": lambda x: x + 273.15,
    "C": lambda x: x + 273.15,
    "°F": lambda x: (x - 32) * 5/9 + 273.15,
    "F": lambda x: (x - 32) * 5/9 + 273.15,
    "K": lambda x: x,
    
    # Pressure -> Pascal
    "Pa": lambda x: x,
    "hPa": lambda x: x * 100,
    "kPa": lambda x: x * 1000,
    "bar": lambda x: x * 100000,
    "mbar": lambda x: x * 100,
    "psi": lambda x: x * 6894.76,
    "atm": lambda x: x * 101325,
    
    # Length -> meters
    "mm": lambda x: x / 1000,
    "cm": lambda x: x / 100,
    "m": lambda x: x,
    "km": lambda x: x * 1000,
    "in": lambda x: x * 0.0254,
    "ft": lambda x: x * 0.3048,
    
    # Time -> seconds
    "ms": lambda x: x / 1000,
    "s": lambda x: x,
    "min": lambda x: x * 60,
    "h": lambda x: x * 3600,
    
    # Voltage -> Volts
    "mV": lambda x: x / 1000,
    "V": lambda x: x,
    
    # Current -> Amperes
    "µA": lambda x: x / 1000000,
    "mA": lambda x: x / 1000,
    "A": lambda x: x,
    
    # Power -> Watts
    "mW": lambda x: x / 1000,
    "W": lambda x: x,
    "kW": lambda x: x * 1000,
    
    # Resistance -> Ohms
    "Ω": lambda x: x,
    "kΩ": lambda x: x * 1000,
    "MΩ": lambda x: x * 1000000,
    
    # Frequency -> Hz
    "Hz": lambda x: x,
    "kHz": lambda x: x * 1000,
    "MHz": lambda x: x * 1000000,
    
    # Velocity -> m/s
    "m/s": lambda x: x,
    "km/h": lambda x: x / 3.6,
    
    # Direct values
    "%": lambda x: x,
    "RH": lambda x: x,
    "%RH": lambda x: x,
    "lux": lambda x: x,
    "lx": lambda x: x,
    "rpm": lambda x: x,
}


def parse_value(text: str) -> Tuple[float, Optional[Unit]]:
    """
    Parse a value with optional unit from text.
    
    Args:
        text: String like "25°C", "1000hPa", "50%"
        
    Returns:
        Tuple of (float value, Unit object or None)
        
    Examples:
        >>> parse_value("25°C")
        (25.0, Unit(value=25.0, unit_type='temperature', symbol='°C'))
        >>> parse_value("42")
        (42.0, None)
    """
    text = text.strip()
    
    # Try to match number with unit
    # Sort by length descending to match longer units first (e.g., "kHz" before "Hz")
    sorted_symbols = sorted(UNIT_SYMBOLS.keys(), key=len, reverse=True)
    
    for symbol in sorted_symbols:
        # Escape special regex characters
        escaped_symbol = re.escape(symbol)
        pattern = rf'^(-?\d+\.?\d*)\s*{escaped_symbol}$'
        match = re.match(pattern, text)
        if match:
            value = float(match.group(1))
            return value, Unit(value=value, unit_type=UNIT_SYMBOLS[symbol], symbol=symbol)
    
    # Try to parse as plain number
    try:
        value = float(text)
        return value, None
    except ValueError:
        raise ValueError(f"Cannot parse value: {text}")


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a value from one unit to another.
    
    Args:
        value: The numeric value to convert
        from_unit: Source unit symbol
        to_unit: Target unit symbol
        
    Returns:
        Converted value
    """
    if from_unit not in UNIT_SYMBOLS or to_unit not in UNIT_SYMBOLS:
        raise ValueError(f"Unknown unit: {from_unit} or {to_unit}")
    
    if UNIT_SYMBOLS[from_unit] != UNIT_SYMBOLS[to_unit]:
        raise ValueError(f"Cannot convert between different unit types: {from_unit} and {to_unit}")
    
    # Convert to SI, then to target
    si_value = UNIT_CONVERTERS[from_unit](value)
    
    # Inverse conversion (we need to find the inverse)
    # For simplicity, we'll use a lookup table for common conversions
    return _inverse_convert(si_value, to_unit)


def _inverse_convert(si_value: float, to_unit: str) -> float:
    """Convert from SI base unit to target unit."""
    inverse_converters = {
        # Temperature from Kelvin
        "°C": lambda x: x - 273.15,
        "C": lambda x: x - 273.15,
        "°F": lambda x: (x - 273.15) * 9/5 + 32,
        "F": lambda x: (x - 273.15) * 9/5 + 32,
        "K": lambda x: x,
        
        # Pressure from Pascal
        "Pa": lambda x: x,
        "hPa": lambda x: x / 100,
        "kPa": lambda x: x / 1000,
        "bar": lambda x: x / 100000,
        "mbar": lambda x: x / 100,
        
        # Length from meters
        "mm": lambda x: x * 1000,
        "cm": lambda x: x * 100,
        "m": lambda x: x,
        "km": lambda x: x / 1000,
        
        # Time from seconds
        "ms": lambda x: x * 1000,
        "s": lambda x: x,
        "min": lambda x: x / 60,
        "h": lambda x: x / 3600,
        
        # Voltage from Volts
        "mV": lambda x: x * 1000,
        "V": lambda x: x,
        
        # Current from Amperes
        "µA": lambda x: x * 1000000,
        "mA": lambda x: x * 1000,
        "A": lambda x: x,
        
        # Direct values
        "%": lambda x: x,
        "lux": lambda x: x,
        "lx": lambda x: x,
    }
    
    if to_unit in inverse_converters:
        return inverse_converters[to_unit](si_value)
    
    raise ValueError(f"Cannot convert to unit: {to_unit}")
