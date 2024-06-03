import asyncio
from bleak import BleakClient

# Replace with your device's MAC address and the UUID you want to listen to
device_address = "XX:XX:XX:XX:XX:XX"
characteristic_uuid = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"

async def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    print(f"Notification from {sender}: {data}")

async def main(address, uuid):
    async with BleakClient(address) as client:
        await client.start_notify(uuid, notification_handler)
        print(f"Connected to {address} and listening to UUID {uuid}...")
        await asyncio.sleep(30)  # Listen for 30 seconds
        await client.stop_notify(uuid)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(device_address, characteristic_uuid))
