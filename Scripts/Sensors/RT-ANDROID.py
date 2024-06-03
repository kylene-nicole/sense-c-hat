import serial
import time
import logging
import subprocess

# Replace '/dev/ttyUSB0' 
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='/var/log/update_time.log',
                    filemode='a')

def send_get_time_command():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        
        if ser.isOpen():
            logging.info(f"Serial port {SERIAL_PORT} opened successfully.")
        else:
            logging.error(f"Failed to open serial port {SERIAL_PORT}.")
            return
        
        command = "GET_TIME"  
        ser.write(command.encode('utf-8'))
        logging.info(f"Sent command: {command.strip()}")
        
        time.sleep(1)  
        response = ser.read(ser.in_waiting).decode('utf-8').strip()
        
        if response:
            logging.info(f"Received response: {response}")
            update_system_time(response)
        else:
            logging.warning("No response received.")
        
        ser.close()
        logging.info("Serial connection closed.")
    
    except Exception as e:
        logging.error(f"Error: {e}")

def update_system_time(time_string):
    try:
        # Format the received time (Assuming the format is 'YYYY-MM-DD HH:MM:SS')
        formatted_time = time_string
        
        # Update the system time using the `date` command
        subprocess.run(['sudo', 'date', '-s', formatted_time], check=True)
        logging.info(f"System time updated to: {formatted_time}")
    
    except Exception as e:
        logging.error(f"Failed to update system time: {e}")

if __name__ == "__main__":
    send_get_time_command()
