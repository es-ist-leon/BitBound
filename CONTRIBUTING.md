# Contributing to BitBound

First off, thank you for considering contributing to BitBound! It's people like you that make BitBound such a great tool for the maker community.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct: be respectful, inclusive, and constructive.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, configuration)
- **Describe the behavior you observed and what you expected**
- **Include your environment** (Python version, MicroPython version, board type)

### Suggesting Enhancements

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Explain why this enhancement would be useful**
- **List any alternatives you've considered**

### Adding New Device Drivers

We welcome new device drivers! Here's how:

1. **Create a new file** in the appropriate directory:
   - Sensors: `bitbound/devices/sensors/`
   - Actuators: `bitbound/devices/actuators/`
   - Displays: `bitbound/devices/displays/`

2. **Follow the existing patterns**:
   ```python
   from ...device import Sensor, DeviceInfo
   
   class MyNewSensor(Sensor):
       def __init__(self, bus, address=0x42, name="MySensor"):
           super().__init__(bus, address, name)
       
       def connect(self) -> bool:
           # Initialize hardware
           self._connected = True
           return True
       
       def disconnect(self) -> None:
           self._connected = False
       
       def get_info(self) -> DeviceInfo:
           return DeviceInfo(
               device_type="sensor",
               name=self._name,
               # ...
           )
       
       @property
       def value(self) -> float:
           # Read from hardware or simulation
           return 42.0
   ```

3. **Add to `__init__.py`** in the appropriate package

4. **Register in `hardware.py`**:
   ```python
   register_device("sensors", "MYSENSOR", MyNewSensor)
   ```

5. **Add tests** in `tests/`

6. **Update documentation**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code, add tests
3. Ensure the test suite passes: `pytest tests/`
4. Make sure your code follows the existing style
5. Write a clear PR description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/bitbound.git
cd bitbound

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black bitbound/

# Type checking (optional)
mypy bitbound/
```

## Style Guidelines

- Follow PEP 8
- Use type hints where practical
- Document public methods with docstrings
- Keep lines under 100 characters (configured in pyproject.toml)

## Testing

- Write tests for new features
- Ensure simulation mode works (tests run without hardware)
- Test on MicroPython if possible

## Project Structure

```
bitbound/
├── __init__.py          # Main exports
├── hardware.py          # Hardware manager & device registry
├── device.py            # Base classes
├── event.py             # Event system
├── expression.py        # Threshold expression parser
├── units.py             # Unit handling
├── buses/               # Bus implementations
└── devices/
    ├── sensors/         # Sensor drivers
    ├── actuators/       # Actuator drivers
    └── displays/        # Display drivers
```

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
