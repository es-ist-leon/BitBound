"""
Base bus interface and types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class BusType(Enum):
    """Supported bus types."""
    I2C = "I2C"
    SPI = "SPI"
    GPIO = "GPIO"
    UART = "UART"
    ONEWIRE = "OneWire"
    CAN = "CAN"
    PWM = "PWM"
    ADC = "ADC"
    DAC = "DAC"


@dataclass
class BusConfig:
    """Configuration for a bus interface."""
    bus_type: BusType
    pins: Dict[str, int] = None
    speed: int = 0
    mode: int = 0
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.pins is None:
            self.pins = {}
        if self.extra is None:
            self.extra = {}


class Bus(ABC):
    """
    Abstract base class for all bus protocols.
    
    Provides a unified interface for hardware communication.
    """
    
    def __init__(self, config: Optional[BusConfig] = None):
        """
        Initialize the bus.
        
        Args:
            config: Bus configuration
        """
        self._config = config or BusConfig(bus_type=BusType.GPIO)
        self._initialized = False
        self._simulation_mode = True  # Default to simulation
    
    @property
    def bus_type(self) -> BusType:
        """Get the bus type."""
        return self._config.bus_type
    
    @property
    def is_simulation(self) -> bool:
        """Check if running in simulation mode."""
        return self._simulation_mode
    
    @abstractmethod
    def init(self) -> bool:
        """
        Initialize the bus.
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def deinit(self) -> None:
        """Deinitialize the bus."""
        pass
    
    @abstractmethod
    def scan(self) -> List[int]:
        """
        Scan for devices on the bus.
        
        Returns:
            List of device addresses found
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.init()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.deinit()
        return False


class BusFactory:
    """Factory for creating bus instances."""
    
    _bus_classes: Dict[str, type] = {}
    
    @classmethod
    def register(cls, bus_type: str, bus_class: type) -> None:
        """Register a bus class."""
        cls._bus_classes[bus_type.upper()] = bus_class
    
    @classmethod
    def create(cls, bus_type: str, **kwargs) -> Bus:
        """
        Create a bus instance.
        
        Args:
            bus_type: Type of bus ("I2C", "SPI", etc.)
            **kwargs: Bus-specific configuration
            
        Returns:
            Bus instance
        """
        bus_type = bus_type.upper()
        if bus_type not in cls._bus_classes:
            raise ValueError(f"Unknown bus type: {bus_type}")
        
        return cls._bus_classes[bus_type](**kwargs)
    
    @classmethod
    def available_types(cls) -> List[str]:
        """Get list of available bus types."""
        return list(cls._bus_classes.keys())
