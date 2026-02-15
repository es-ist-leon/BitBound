"""
Async Monitoring Example

Uses async support to read multiple sensors concurrently
and log data with the DataLogger.
"""

import asyncio
from bitbound import Hardware
from bitbound.async_support import AsyncDevice, gather_readings
from bitbound.logging import DataLogger, RingBuffer

# Setup hardware
hw = Hardware()
temp_sensor = hw.attach("I2C", type="BME280")
light_sensor = hw.attach("I2C", type="BH1750")

# Setup logging
logger = DataLogger("environment", format="csv", max_entries=10000)
temp_buffer = RingBuffer(60)  # Last 60 readings


async def monitor():
    """Main monitoring loop."""
    while True:
        # Read sensors concurrently
        results = await gather_readings(
            [temp_sensor, light_sensor],
            ["temperature", "lux"]
        )

        temp = results[0]
        lux = results[1]

        # Log data
        logger.log({"temperature": temp, "lux": lux})
        temp_buffer.append(temp)

        # Print stats
        print(f"Temp: {temp}°C (avg: {temp_buffer.average():.1f}°C) | Light: {lux} lux")

        await asyncio.sleep(1)


asyncio.run(monitor())
