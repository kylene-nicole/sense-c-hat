import time
import logging
from logging.handlers import TimedRotatingFileHandler
import smbus
import math
from SHTC3 import SHTC3 
from IMU import IMU 

# SHTC3 start
import lgpio as sbc

SHTC3_I2C_ADDRESS   = 0x70

SHTC3_ID            = 0xEFC8
CRC_POLYNOMIAL      = 0x0131
SHTC3_WakeUp        = 0x3517
SHTC3_Sleep         = 0xB098
SHTC3_Software_RES  = 0x805D
SHTC3_NM_CD_ReadTH  = 0x7866
SHTC3_NM_CD_ReadRH  = 0x58E0
# SHTC3 end

# IMU start
q0 = 1.0
q1 = q2 = q3 = 0.0
angles = [0.0, 0.0, 0.0]
# IMU end


# define QMI8658 and AK09918 Device I2C address
I2C_ADD_IMU_QMI8658                  = 0x6B
I2C_ADD_IMU_AK09918                  = 0x0C

# define QMI8658 Register
QMI8658_CTRL7_ACC_ENABLE    = 0x01
QMI8658_CTRL7_GYR_ENABLE    = 0x02

QMI8658Register_Ctrl1       = 0x02 # SPI Interface and Sensor Enable
QMI8658Register_Ctrl2       = 0x03 # Accelerometer control.
QMI8658Register_Ctrl3       = 0x04 # Gyroscope control.
QMI8658Register_Ctrl5       = 0x06 # Data processing settings.
QMI8658Register_Ctrl7       = 0x08 # Sensor enabled status.

QMI8658Register_Ax_L        = 0x35 # Accelerometer X axis least significant byte.
QMI8658Register_Ax_H        = 0x36 # Accelerometer X axis most significant byte.
QMI8658Register_Ay_L        = 0x37 # Accelerometer Y axis least significant byte.
QMI8658Register_Ay_H        = 0x38 # Accelerometer Y axis most significant byte.
QMI8658Register_Az_L        = 0x39 # Accelerometer Z axis least significant byte.
QMI8658Register_Az_H        = 0x3A # Accelerometer Z axis most significant byte.
QMI8658Register_Gx_L        = 0x3B # Gyroscope X axis least significant byte.
QMI8658Register_Gx_H        = 0x3C # Gyroscope X axis most significant byte.
QMI8658Register_Gy_L        = 0x3D # Gyroscope Y axis least significant byte.
QMI8658Register_Gy_H        = 0x3E # Gyroscope Y axis most significant byte.
QMI8658Register_Gz_L        = 0x3F # Gyroscope Z axis least significant byte.
QMI8658Register_Gz_H        = 0x40 # Gyroscope Z axis most significant byte.

QMI8658Register_Tempearture_L = 0x33 # tempearture low.
QMI8658Register_Tempearture_H = 0x34 # tempearture high.

QMI8658AccRange_2g          = 0x00 << 4 # !< \brief +/- 2g range
QMI8658AccRange_4g          = 0x01 << 4 # !< \brief +/- 4g range
QMI8658AccRange_8g          = 0x02 << 4 # !< \brief +/- 8g range
QMI8658AccRange_16g         = 0x03 << 4 # !< \brief +/- 16g range

QMI8658AccOdr_8000Hz        = 0x00 # !< \brief High resolution 8000Hz output rate.
QMI8658AccOdr_4000Hz        = 0x01 # !< \brief High resolution 4000Hz output rate. 
QMI8658AccOdr_2000Hz        = 0x02 # !< \brief High resolution 2000Hz output rate.
QMI8658AccOdr_1000Hz        = 0x03 # !< \brief High resolution 1000Hz output rate.
QMI8658AccOdr_500Hz         = 0x04 # !< \brief High resolution 500Hz output rate.
QMI8658AccOdr_250Hz         = 0x05 # !< \brief High resolution 250Hz output rate.
QMI8658AccOdr_125Hz         = 0x06 # !< \brief High resolution 125Hz output rate.
QMI8658AccOdr_62_5Hz        = 0x07 # !< \brief High resolution 62.5Hz output rate.
QMI8658AccOdr_31_25Hz       = 0x08 # !< \brief High resolution 31.25Hz output rate.
QMI8658AccOdr_LowPower_128Hz = 0x0C # !< \brief Low power 128Hz output rate.
QMI8658AccOdr_LowPower_21Hz  = 0x0D # !< \brief Low power 21Hz output rate.
QMI8658AccOdr_LowPower_11Hz  = 0x0E # !< \brief Low power 11Hz output rate.
QMI8658AccOdr_LowPower_3Hz   = 0x0F # !< \brief Low power 3Hz output rate.

QMI8658GyrRange_16dps       = 0 << 4 # !< \brief +-16 degrees per second. 
QMI8658GyrRange_32dps       = 1 << 4 # !< \brief +-32 degrees per second. 
QMI8658GyrRange_64dps       = 2 << 4 # !< \brief +-64 degrees per second. 
QMI8658GyrRange_128dps      = 3 << 4 # !< \brief +-128 degrees per second. 
QMI8658GyrRange_256dps      = 4 << 4 # !< \brief +-256 degrees per second. 
QMI8658GyrRange_512dps      = 5 << 4 # !< \brief +-512 degrees per second. 
QMI8658GyrRange_1024dps     = 6 << 4 # !< \brief +-1024 degrees per second. 
QMI8658GyrRange_248dps      = 7 << 4 # !< \brief +-2048 degrees per second. 

QMI8658GyrOdr_8000Hz        = 0x00 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_4000Hz        = 0x01 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_2000Hz        = 0x02 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_1000Hz        = 0x03 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_500Hz         = 0x04 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_250Hz         = 0x05 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_125Hz         = 0x06 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_62_5Hz        = 0x07 # !< \brief High resolution 8000Hz output rate.
QMI8658GyrOdr_31_25Hz       = 0x08 # !< \brief High resolution 8000Hz output rate.

# define QMI8658 Register  end

# define AK09918 Register
AK09918_WIA1       = 0x00    # Company ID
AK09918_WIA2       = 0x01    # Device ID
AK09918_RSV1       = 0x02    # Reserved 1
AK09918_RSV2       = 0x03    # Reserved 2
AK09918_ST1        = 0x10    # DataStatus 1
AK09918_HXL        = 0x11    # X-axis data 
AK09918_HXH        = 0x12
AK09918_HYL        = 0x13    # Y-axis data
AK09918_HYH        = 0x14
AK09918_HZL        = 0x15    # Z-axis data
AK09918_HZH        = 0x16
AK09918_TMPS       = 0x17    # Dummy
AK09918_ST2        = 0x18    # Datastatus 2
AK09918_CNTL1      = 0x30    # Dummy
AK09918_CNTL2      = 0x31    # Control settings
AK09918_CNTL3      = 0x32    # Control settings

AK09918_SRST_BIT   = 0x01    # Soft Reset
AK09918_HOFL_BIT   = 0x08    # Sensor Over Flow
AK09918_DOR_BIT    = 0x02    # Data Over Run
AK09918_DRDY_BIT   = 0x01    # Data Ready


AK09918_POWER_DOWN = 0x00
AK09918_NORMAL     = 0x01
AK09918_CONTINUOUS_10HZ  = 0x02
AK09918_CONTINUOUS_20HZ  = 0x04
AK09918_CONTINUOUS_50HZ  = 0x06
AK09918_CONTINUOUS_100HZ = 0x08
AK09918_SELF_TEST         = 0x10 # ignored by switchMode() and initialize(), call selfTest() to use this mode
# define AK09918 Register  end

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
        "roll": math.asin(-2 * q1 * q3 + 2 * q0 * q2) * 57.3,
        "pitch": math.atan2(2 * q2 * q3 + 2 * q0 * q1, -2 * q1 * q1 - 2 * q2 * q2 + 1) * 57.3,
        "yaw": math.atan2(-2 * q1 * q2 - 2 * q0 * q3, 2 * q2 * q2 + 2 * q3 * q3 - 1) * 57.3,
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
