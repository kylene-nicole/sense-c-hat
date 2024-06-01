#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
from datetime import datetime
import lgpio as sbc
import csv
import logging 
from logging.handlers import RotatingFileHandler
# SHTC3 sensor

SHTC3_I2C_ADDRESS   = 0x70

SHTC3_ID            = 0xEFC8
CRC_POLYNOMIAL      = 0x0131
SHTC3_WakeUp        = 0x3517
SHTC3_Sleep         = 0xB098
SHTC3_Software_RES  = 0x805D
SHTC3_NM_CD_ReadTH  = 0x7866
SHTC3_NM_CD_ReadRH  = 0x58E0


# Set up logging
log_file = "/home/$(whoami)/sense-c-hat/logs/temp_hum.log"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TEMP-HUM")
handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class SHTC3():
    def __init__(self,sbc,bus,address,flags = 0):
        try:
            self._sbc = sbc
            self._fd = self._sbc.i2c_open(bus, address, flags)
            self.SHTC_SOFT_RESET()
        except Exception as e:
            with open(log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "error"])
                writer.writerow([datetime.now(), f"Failed to initialize SHTC3 sensor: {str(e)}"])
            raise

    def SHTC3_CheckCrc(self,data,len,checksum):
        crc = 0xFF
        for byteCtr in range(0,len):
            crc = crc ^ data[byteCtr]
            for bit in range(0,8):
                if crc & 0x80:
                    crc = (crc << 1) ^ CRC_POLYNOMIAL
                else:
                    crc = crc << 1
        if crc == checksum:
            return True
        else:
            return False
    
    def SHTC3_WriteCommand(self,cmd):
        self._sbc.i2c_write_byte_data(self._fd,cmd >> 8,cmd & 0xFF)
    
    def SHTC3_WAKEUP(self):
        self.SHTC3_WriteCommand(SHTC3_WakeUp) # write wake_up command
        time.sleep(0.01) # Prevent the system from crashing 
    
    def SHTC3_SLEEP(self):
        self.SHTC3_WriteCommand(SHTC3_Sleep) # Write sleep command
        time.sleep(0.01)
    
    def SHTC_SOFT_RESET(self):
        self.SHTC3_WriteCommand(SHTC3_Software_RES) # Write reset command
        time.sleep(0.01)
    
    def SHTC3_Read_TH(self): # Read temperature 
        try:
            self.SHTC3_WAKEUP()
            self.SHTC3_WriteCommand(SHTC3_NM_CD_ReadTH)
            time.sleep(0.02)
            (count, buf) = self._sbc.i2c_read_device(self._fd, 3)
            if self.SHTC3_CheckCrc(buf, 2, buf[2]):
                return (buf[0] << 8 | buf[1]) * 175 / 65536 - 45.0
            else:
                with open(log_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([datetime.now(), "CRC error in temperature reading"])
                return None
        except Exception as e:
            with open(log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now(), f"Error reading temperature: {str(e)}"])
            return None
    
    def SHTC3_Read_RH(self): # Read humidity 
        try:
            self.SHTC3_WAKEUP()
            self.SHTC3_WriteCommand(SHTC3_NM_CD_ReadRH)
            time.sleep(0.02)
            (count, buf) = self._sbc.i2c_read_device(self._fd, 3)
            if self.SHTC3_CheckCrc(buf, 2, buf[2]):
                return 100 * (buf[0] << 8 | buf[1]) / 65536
            else:
                with open(log_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([datetime.now(), "CRC error in humidity reading"])
                return None
        except Exception as e:
            with open(log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now(), f"Error reading humidity: {str(e)}"])
            return None


if __name__ == "__main__":
    try:
        shtc3 = SHTC3(sbc, 1, SHTC3_I2C_ADDRESS)
        
        # Write CSV header
        with open(log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "temperature", "humidity"])

        while True:
            temperature = shtc3.SHTC3_Read_TH()
            humidity = shtc3.SHTC3_Read_RH()
            if temperature is not None and humidity is not None:
                with open(log_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([datetime.now(), temperature, humidity])
            time.sleep(1)
    except Exception as e:
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now(), f"Exception in main loop: {str(e)}"])
        print("\nProgram ended due to an error:", e)