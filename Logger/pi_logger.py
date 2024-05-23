import time
import logging
from logging.handlers import TimedRotatingFileHandler
import smbus
import math
from SHTC3 import SHTC3 
from IMU import IMU 

# Setup logging
def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')  
    handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

temp_humidity_logger = setup_logger('Temperature_Humidity', 'temp_humidity.log')
imu_logger = setup_logger('IMU', 'imu.log')

def log_temp_humidity(shtc3):
    temp = shtc3.SHTC3_Read_TH()
    humidity = shtc3.SHTC3_Read_RH()
    temp_humidity_logger.info(f"Temperature = {temp:.2f}°C, Humidity = {humidity:.2f}%")

def log_imu(imu_sensor):
    imu_sensor.QMI8658_Gyro_Accel_Read()
    imu_sensor.AK09918_MagRead()
    imu_sensor.icm20948CalAvgValue()
    imu_sensor.imuAHRSupdate(imu_sensor.MotionVal[0] * 0.0175, imu_sensor.MotionVal[1] * 0.0175, imu_sensor.MotionVal[2] * 0.0175,
                             imu_sensor.MotionVal[3], imu_sensor.MotionVal[4], imu_sensor.MotionVal[5], 
                             imu_sensor.MotionVal[6], imu_sensor.MotionVal[7], imu_sensor.MotionVal[8])
    imu_data = {
        "roll": math.asin(-2 * imu_sensor.q1 * imu_sensor.q3 + 2 * imu_sensor.q0 * imu_sensor.q2) * 57.3,
        "pitch": math.atan2(2 * imu_sensor.q2 * imu_sensor.q3 + 2 * imu_sensor.q0 * imu_sensor.q1, -2 * imu_sensor.q1 * imu_sensor.q1 - 2 * imu_sensor.q2 * imu_sensor.q2 + 1) * 57.3,
        "yaw": math.atan2(-2 * imu_sensor.q1 * imu_sensor.q2 - 2 * imu_sensor.q0 * imu_sensor.q3, 2 * imu_sensor.q2 * imu_sensor.q2 + 2 * imu_sensor.q3 * imu_sensor.q3 - 1) * 57.3,
        "temp": imu_sensor.QMI8658_readTemp(),
        "accel_x": imu_sensor.Accel[0],
        "accel_y": imu_sensor.Accel[1],
        "accel_z": imu_sensor.Accel[2],
        "gyro_x": imu_sensor.Gyro[0],
        "gyro_y": imu_sensor.Gyro[1],
        "gyro_z": imu_sensor.Gyro[2],
        "mag_x": imu_sensor.Mag[0],
        "mag_y": imu_sensor.Mag[1],
        "mag_z": imu_sensor.Mag[2]
    }
    imu_logger.info(str(imu_data))

if __name__ == "__main__":
    shtc3 = SHTC3(sbc, 1, SHTC3_I2C_ADDRESS)
    imu_sensor = IMU()

    try:
        while True:
            log_temp_humidity(shtc3)
            log_imu(imu_sensor)
            time.sleep(1)  
    except KeyboardInterrupt:
        print("\nProgram terminated manually")
        exit()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        exit()
