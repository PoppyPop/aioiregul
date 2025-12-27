"""Example: Using the IRegul v2 socket client to fetch device data."""

import asyncio

from aioiregul.v2 import IRegulClient


async def main():
    """
    Connect to an IRegul device and fetch data using the v2 socket client.

    This example demonstrates:
    1. Creating a client instance
    2. Fetching mapped data (typed models)
    3. Displaying the results
    """
    # Create a client (uses default host/port for i-regul.fr:443)
    client = IRegulClient(
        host="i-regul.fr",
        port=443,
        username="empty",
        device_key="REDACTED",
    )

    try:
        print("Connecting to IRegul device...")
        print()

        # Fetch data with 502 command (full data with parameters/labels)
        # Returns mapped data (typed models) by default
        data = await client.get_data(device_id="REDACTED", timeout=60, mapped=True)

        print("✓ Successfully retrieved device data")
        print()
        print("Device Data Summary:")
        print(f"  Timestamp: {data['timestamp']}")
        print(f"  Zones: {len(data['zones'])}")
        print(f"  Inputs: {len(data['inputs'])}")
        print(f"  Outputs: {len(data['outputs'])}")
        print(f"  Measurements: {len(data['measurements'])}")
        print(f"  Parameters: {len(data['parameters'])}")
        print(f"  Labels: {len(data['labels'])}")
        print(f"  Analog Sensors: {len(data['analog_sensors'])}")
        print(f"  Modbus Registers: {len(data['modbus_registers'])}")
        print()

        # Display sample measurements
        print("Sample Measurements (first 5):")
        for measurement in data["measurements"][:5]:
            if isinstance(measurement, dict):
                print(
                    f"  - {measurement.get('index')}: "
                    f"{measurement.get('valeur')} {measurement.get('unit', '')}"
                )

        print()

        # Display sample parameters
        print("Sample Parameters (first 5):")
        for param in data["parameters"][:5]:
            if isinstance(param, dict):
                print(f"  - {param.get('index')}: {param.get('valeur')} {param.get('unit', '')}")

    except asyncio.TimeoutError:
        print("✗ Connection timeout - device did not respond within 60 seconds")
    except ConnectionError as e:
        print(f"✗ Connection failed: {e}")
    except ValueError as e:
        print(f"✗ Invalid response: {e}")


if __name__ == "__main__":
    asyncio.run(main())
