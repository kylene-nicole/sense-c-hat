import os
import serial
import serial.tools.list_ports
from serial.tools import list_ports
import pandas as pd
import numpy as np
import json
import time
import datetime 
import csv 
import logging

OPS24x_CW_Sampling_Freq10 = 'S1'      # 10Ksps
OPS24x_CW_Sampling_Freq20 = 'S2'      # 20Ksps

OPS24x_CW_Sampling_Size128 = 'S('     # 128 data size
OPS24x_CW_Sampling_Size256 = 'S['     # 256 data size
OPS24x_CW_Sampling_Size512 = 'S<'     # 512 data size
OPS24x_CW_Sampling_Size1024 = 'S>'    # 1024 data size

OPS24x_FMCW_Sampling_Size128 = 's('   # 128 data size
OPS24x_FMCW_Sampling_Size256 = 's['   # 256 data size
OPS24x_FMCW_Sampling_Size512 = 's<'   # 512 data size
OPS24x_FMCW_Sampling_Size1024 = 's>'  # 1024 data size

OPS24x_CW_FFT_Scale1 = 'X1'           # FFT size = 1x data size
OPS24x_CW_FFT_Scale2 = 'X2'           # FFT size = 2x data size
OPS24x_CW_FFT_Scale4 = 'X4'           # FFT size = 4x data size
OPS24x_CW_FFT_Scale8 = 'X8'           # FFT size = 8x data size

OPS24x_FMCW_FFT_Scale1 = 'x1'         # FFT size = 1x data size
OPS24x_FMCW_FFT_Scale2 = 'x2'         # FFT size = 2x data size
OPS24x_FMCW_FFT_Scale4 = 'x4'         # FFT size = 4x data size
OPS24x_FMCW_FFT_Scale8 = 'x8'         # FFT size = 8x data size

OPS24x_Blanks_Send_Zeros = 'BZ'
OPS24x_Blanks_Send_Void = 'BV'

OPS24x_Query_Product = '?P'

OPS24x_Power_Idle = 'PI'             # IDLE power
OPS24x_Power_Min = 'PN'              # Min power
OPS24x_Power_Mid = 'PD'              # Medium power
OPS24x_Power_Max = 'PX'              # Max power
OPS24x_Power_Active = 'PA'           # power ACTIVE
OPS24x_Power_Pulse = 'PP'            # PULSE power

OPS24x_Wait_1kms = 'WM'              # Wait 1000 ms between readings
OPS24x_Wait_500ms = 'WD'             # Wait 500 ms between readings
OPS24x_Wait_200ms = 'W2'             # Wait 200 ms between readings
OPS24x_Wait_100ms = 'WC'             # Wait 100 ms between readings

OPS24x_Output_Speed = 'OS'           # send speed value
OPS24x_Output_No_Speed = 'Os'        # don't send speed value
OPS24x_Output_Distance = 'OD'        # send distance values
OPS24x_Output_No_Distance = 'Od'     # don't send distance values
OPS24x_Output_JSONy_data = 'OJ'      # send JSON formatted data
OPS24x_Output_No_JSONy_data = 'Oj'   # don't send JSON formatted data

OPS24x_Output_No_Binary_data = 'Ob'  # don't use binary mode

OPS24x_Output_CW_Raw = 'OR'          # send CW raw data
OPS24x_Output_No_CW_Raw = 'Or'       # don't send CW raw data
OPS24x_Output_CW_FFT = 'OF'          # send CW FFT data
OPS24x_Output_No_CW_FFT = 'Of'       # don't send CW FFT data
OPS24x_Output_FMCW_Raw = 'oR'        # send FMCW raw data
OPS24x_Output_No_FMCW_Raw = 'or'     # don't send FMCW raw data
OPS24x_Output_FMCW_FFT = 'oF'        # send FMCW FFT data
OPS24x_Output_No_FMCW_FFT = 'of'     # don't send FMCW FFT data

OPS24x_Output_CW_Mag = 'OM'          # send CW magnitudes
OPS24x_Output_No_CW_Mag = 'Om'       # send no CW magnitudes
OPS24x_Output_FMCW_Mag = 'oM'        # send FMCW magnitudes
OPS24x_Output_No_FMCW_Mag = 'om'     # send no FMCW magnitudes

# Set up logging - this needs to be edited, see rasp pi v1.1 for ref
log_file = "/home/$(whoami)/sense-c-hat/logs/ops_radar.log"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OPS-RADAR")
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# csv_directory = "csv_files-" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
username = os.environ.get('USERNAME') or os.environ.get('USER')
base_directory = f"C:\\Users\\{username}\\Documents\\TestingData\\OPS\\RawOPS"
os.makedirs(base_directory, exist_ok=True)
csv_directory = os.path.join(base_directory, "csv_files-" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
os.makedirs(csv_directory, exist_ok=True)

# change this depending on testing tech laptop config
predefined_stations = {
    '1': ['COM6', 'COM7'], # ['COM6', 'COM8'], changed to com 3 for testing 
    '2': ['COM16', 'COM17']
}

resolutions = {
    '128': 's(',
    '256': 's[',
    '512': 's<',
    '1024': 's>' 
}

class Radar:
    def __init__(self, device_port, station_number): #, freq_key, freq_val):
        self.values_I = None
        self.values_Q = None
        self.values_FFT = None
        self.np_values = None
        self.np_values_I = None
        self.np_values_Q = None
        self.np_values_FFT = None
        self.power_dbm = None
        self.csv_file_name = None
        self.device_port = device_port
        self.station_number = station_number
        # self.freq_key = freq_key
        # self.freq_val = freq_val

        try:
            self.radar = serial.Serial(
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1,
                writeTimeout=2
            ) 

            # OPEN RADAR SERIAL PORT & FLUSH
            self.radar.port = device_port
            if not self.radar.is_open:
                self.radar.open()

            self.radar.flushInput()
            self.radar.flushOutput()

            self.radar_api_config()
        except Exception as e:
            logger.error("Failed to initialize radar: %s", str(e))
            raise
    
    def radar_api_config(self):
        # config = ['OJ', 'oR', 'oM', 'OS', 'oF', self.freq_val, 'PA']
        try:
            config = ['OJ', 'oR', 'oM', 'OS', 'oF', 'PA']

            for command in config:
                data_for_send_str = command + '\n'
                data_for_send_bytes = str.encode(data_for_send_str)
                self.radar.write(data_for_send_bytes)

            
                logging.debug("Radar initialized")
        except Exception as e:
            logger.error("Error in radar_api_config: %s", str(e))
            raise
    
    def collect_and_save_data(self):
        self.radar.reset_input_buffer()
        
        # update the csv file name to match the UI from testing tech
        file_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # self.csv_file_name = f"radar_{self.device_port}_{self.room_number}.{self.station_number}.{self.environment}-test-{self.test_id}.{self.freq_key}_{file_timestamp}.csv"
        self.csv_file_name = f"radar_logs_{file_timestamp}.csv"


        end_time = time.time() + self.duration
        sample_counter = 0

        file_exists = os.path.exists(self.csv_file_name)
        
        csv_path = os.path.join(csv_directory, self.csv_file_name)
        with open(csv_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            
            # CSV headers - if new file
            # TODO - add time stamp to csv file in datetime to the ms
            if not file_exists:
                writer.writerow(["I", "Q", "FFT", "POWER_DBM"])

            # initialize to track the current part of the scan sequence
            scan_part = "I"
            
            while self.radar.is_open and time.time() < end_time:
                data_rx_json = self.radar.readline().decode('utf-8').strip()
                
                try:
                    data = json.loads(data_rx_json)
                    
                    if scan_part in data:
                        if scan_part == "I":
                            self.values_I = data['I']
                            scan_part = "Q" 
                            
                        elif scan_part == "Q":
                            self.values_Q = data['Q']
                            scan_part = "FFT" 
                            
                        elif scan_part == "FFT":
                            self.values_FFT = data['FFT']
                            sample_counter += 1

                            if sample_counter <= 3:
                                scan_part = "I"
                                continue

                            try:
                                self.power_dbm = [10 * np.log10((i * (3.3 / 4096)) ** 2 + (q * (3.3 / 4096)) ** 2) for i, q in zip(self.values_I, self.values_Q)]
                            except Exception as e:
                                scan_part = "I"
                                continue
                            
                            for i, q, fft, power in zip(self.values_I, self.values_Q, self.values_FFT, self.power_dbm):
                                writer.writerow([i, q, fft, power])

                            scan_part = "I"  # Reset 
                            
                except json.JSONDecodeError:
                        logging.error(f"Error decoding JSON: {data_rx_json}")
                except Exception as e:
                        logging.exception("Exception during data collection")
                except KeyboardInterrupt:
                        logging.info("Keyboard interrupt detected")
                        break       

def station_ports(station_number):
    available_ports = [port.device for port in serial.tools.list_ports.comports()]
    logging.debug(f"[DEBUG] Available ports: {available_ports}") 

    station_number = str(station_number)

    # check each predefined station to see if its ports are all present in the available ports
    if station_number in predefined_stations:
        station_ports = predefined_stations[station_number]
        logging.debug(f"[DEBUG] Station ports to match: {station_ports}")
        if all(port in available_ports for port in station_ports):
            logging.debug(f"[DEBUG] Station {station_number} ports found: {station_ports}")
            return station_ports 

    logging.debug("[WARNING] No predefined station port pairings found among available ports.")
    return []

def init_directory():
    if not os.path.exists(csv_directory):
        os.makedirs(csv_directory)

def start_radar_data_collection(station_number):
    logging.basicConfig(filename='run_radar.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    try:

        init_directory()
        radar_ports = station_ports(station_number)
        if radar_ports == []:
            return "Fail"
        # for freq_key, freq_val in resolutions:
        for port in radar_ports:
            logging.debug(f"Serial port: {port}")
            radar = Radar(port, station_number) #, freq_key, freq_val)
            print(f"Starting data collection on {port}...")
            radar.collect_and_save_data()
            radar.radar.close()
            logging.debug(f"Closing radar port: {port}")
        logging.info("Success - Closing all radar ports on station", station_number)
        return "Pass"
    except Exception as e:
        logging.error(f"Error in start_radar_data_collection: {str(e)}")
        return "Fail"
    
if __name__ == "__main__":
    station_number = 1  # Change this as needed
    result = start_radar_data_collection(station_number)
    print(result)