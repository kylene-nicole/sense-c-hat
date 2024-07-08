import asyncio
from bleak import BleakClient
from bleak import BleakScanner
import subprocess
from datetime import datetime
import time

# Replace with your device's name and UUIDs
DEVICE_NAME = "P4"
SERVICE_UUID = "97DFBDEB-6B7C-4EC3-A69B-491155BD22B1"
CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef2"

async def main():
    try:
        device = None

        # Discover devices
        devices = await BleakScanner.discover()
        for d in devices:
            if d.name == DEVICE_NAME:
                device = d
                break

        if not device:
            print(f"Device {DEVICE_NAME} not found.")
            return

        async with BleakClient(device.address) as client:
            try:
                if not client.is_connected:
                    print(f"Failed to connect to {DEVICE_NAME}.")
                    return

                # Read the characteristic value
                value = await client.read_gatt_char(CHARACTERISTIC_UUID)
                timestamp_str = value.decode('utf-8').strip()
                print(f"Received timestamp: {timestamp_str}")

                # Update the system time
                new_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                subprocess.run(['sudo', 'date', '-s', new_time.strftime('%Y-%m-%d %H:%M:%S')])
                print("System time updated successfully.")
                print(new_time)


            except Exception as e:
                print(f"Error: {e}")
    except:
        time.sleep(5)
        main()

if __name__ == "__main__":
    asyncio.run(main())