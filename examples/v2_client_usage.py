"""Example: Using the IRegul socket client to fetch device data.

Before running this example:
1. Copy .env.example to .env
2. Fill in your device details (IREGUL_DEVICE_ID, IREGUL_DEVICE_KEY, etc.)
3. Run this script
"""

import asyncio

from aioiregul.iregulapi import IRegulApiInterface
from aioiregul.v2 import IRegulClient


async def main():
    """
    Connect to an IRegul device and fetch data using the socket client.

    Configuration is loaded from environment variables (.env file).

    This example demonstrates:
    1. Creating a client instance
    2. Fetching mapped data (typed models)
    3. Displaying the results
    """
    # Create a client - configuration loaded from environment variables
    # Required: IREGUL_DEVICE_KEY
    # Optional: IREGUL_HOST, IREGUL_PORT, IREGUL_DEVICE_ID, IREGUL_USERNAME
    client: IRegulApiInterface = IRegulClient()

    try:
        print("Connecting to IRegul device...")
        print()

        # Fetch data with 502 command (full data with parameters/labels)
        # Returns mapped data (typed models)
        data = await client.get_data()

        print("✓ Successfully retrieved device data")
        print()
        print("Device Data Summary:")
        print(f"  Timestamp: {data.timestamp}")
        print(f"  Zones: {len(data.zones)}")
        print(f"  Inputs: {len(data.inputs)}")
        print(f"  Outputs: {len(data.outputs)}")
        print(f"  Measurements: {len(data.measurements)}")
        print(f"  Parameters: {len(data.parameters)}")
        print(f"  Labels: {len(data.labels)}")
        print(f"  Analog Sensors: {len(data.analog_sensors)}")
        print(f"  Modbus Registers: {len(data.modbus_registers)}")
        print()

        # Display sample measurements
        print("Sample Measurements (first 5):")
        for measurement in list(data.measurements.values())[:5]:
            print(f"  - {measurement.index}: {measurement.valeur} {measurement.unit}")

        print()

        # Display sample parameters
        print("Sample Parameters (first 5):")
        for param in list(data.parameters.values())[:5]:
            print(f"  - {param.index} ({param.nom}): {param.valeur}")

    except TimeoutError:
        print("✗ Connection timeout - device did not respond within 60 seconds")
    except ConnectionError as e:
        print(f"✗ Connection failed: {e}")
    except ValueError as e:
        print(f"✗ Invalid response: {e}")


if __name__ == "__main__":
    asyncio.run(main())
