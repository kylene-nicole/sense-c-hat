import serial
import time
import logging
import json

# Radar configuration commands
commands = [
    'OJ',  # Output JSON formatted data
    'oR',  # Output FMCW raw data
    'oM',  # Output FMCW magnitudes
    'OS',  # Output speed value
    'oF',  # Output FMCW FFT data
    'PA',  # Power ACTIVE
    'A!'   # Save configuration in flash memory
]

class Radar:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = serial.Serial(
            port=self.port,
            baudrate=self.baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1,
            write_timeout=2
        )

        if not self.serial_connection.is_open:
            self.serial_connection.open()

        self.serial_connection.flushInput()
        self.serial_connection.flushOutput()

    def set_baud_rate(self, baud_command):
        self.send_command('In' + baud_command)
        self.serial_connection.baudrate = int(baud_command[1:])  # Change the baud rate of the serial connection
        print(f"Baud rate set to {self.serial_connection.baudrate}")


    def send_configuration(self):
        for command in commands:
            self.send_command(command)
            # time.sleep(0.5)  # Delay to ensure command is processed

    def send_command(self, command):
        full_command = f'{command}\n'
        self.serial_connection.write(full_command.encode())

    def read_data(self):
        while True:
            data = self.serial_connection.readline()
            if data:
                try:
                    # Assuming data is in JSON format
                    parsed_data = json.loads(data.decode('utf-8').strip())
                    print("Received:", parsed_data)
                except json.JSONDecodeError:
                    print("Received non-JSON data:", data.decode('utf-8').strip())

    def close(self):
        self.serial_connection.close()

if __name__ == "__main__":
    radar_device_port = 'COM11'
    radar = Radar(radar_device_port, 9600)  # Start with the default baud rate
    try:
        # radar.set_baud_rate('I1')  # Change to 57,600 baud rate
        radar.send_configuration()
        print("Radar configuration sent.")
        radar.read_data()
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        radar.close()
        print("Radar connection closed.")
