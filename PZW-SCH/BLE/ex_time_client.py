import asyncio
from bleak import BleakClient, BleakScanner

device_name = "Pixel 4"
characteristic_uuid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

async def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    print(f"Notification from {sender}: {data}")

async def scan_and_connect(device_name, characteristic_uuid):
    devices = await BleakScanner.discover()
    target_device = None
    for device in devices:
        if device_name in device.name:
            target_device = device
            break

    if not target_device:
        print(f"Device with name {device_name} not found.")
        return

    async with BleakClient(target_device) as client:
        await client.start_notify(characteristic_uuid, notification_handler)
        print(f"Connected to {target_device.name} and listening to UUID {characteristic_uuid}...")
        await asyncio.sleep(30)  # Listen for 30 seconds
        await client.stop_notify(characteristic_uuid)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan_and_connect(device_name, characteristic_uuid))
