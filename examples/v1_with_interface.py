#!/usr/bin/env python3
"""Example usage of v1.Device with the IRegulDeviceInterface protocol.

This example demonstrates:
1. Creating a Device with an HTTP session in the constructor
2. Calling get_data() and defrost() without passing the session each time
3. Typing hints for code that accepts any IRegulDeviceInterface
"""

import asyncio

import aiohttp

from aioiregul.v1 import ConnectionOptions, Device, IRegulApiInterface


async def collect_and_print_data(device: IRegulApiInterface) -> None:
    """Example function that accepts any IRegulDeviceInterface.

    This could accept either v1.Device or v2.IRegulClient since they both
    implement the interface.
    """
    data = await device.get_data()
    if data is not None:
        print(f"Timestamp: {data.timestamp}")
        print(f"Outputs: {len(data.outputs)}")
        print(f"Inputs: {len(data.inputs)}")
        print(f"Measurements: {len(data.measurements)}")
        print(f"Analog Sensors: {len(data.analog_sensors)}")
    else:
        print("No data returned")


async def main() -> None:
    """Main example."""
    # Create connection options
    options = ConnectionOptions()

    # Create an HTTP session (shared across the device lifetime)
    async with aiohttp.ClientSession() as session:
        # Initialize device with session in constructor
        device: IRegulApiInterface = Device(options, session)

        try:
            await collect_and_print_data(device)

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
