import asyncio
from bleak import BleakClient, BleakScanner
from datetime import datetime
import subprocess

# Replace with the Pixel 4 device's name
PIXEL_4_DEVICE_NAME = "P4"

# Replace with the UUID of the characteristic you are reading from
CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef2"

def update_system_time(timestamp_str):
    try:
        # Convert the timestamp string to a datetime object
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        # Format the datetime object to the required format for date command
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Use the date command to set the system time
        subprocess.run(["sudo", "date", "-s", formatted_time])
        print(f"System time updated to: {formatted_time}")
    except ValueError as e:
        print(f"Error parsing timestamp: {e}")

async def notification_handler(sender, data):
    timestamp_str = data.decode("utf-8")
    print(f"Received timestamp: {timestamp_str}")
    update_system_time(timestamp_str)

async def run():
    devices = await BleakScanner.discover()
    pixel_device = None

    for device in devices:
        if device.name == PIXEL_4_DEVICE_NAME:
            pixel_device = device
            break

    if not pixel_device:
        print(f"Device with name '{PIXEL_4_DEVICE_NAME}' not found")
        return

    async with BleakClient(pixel_device.address) as client:
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        print("Listening for notifications...")
        
        # Keep the script running
        while True:
            await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
