import paho.mqtt.client as mqtt
import logging
from logging.handlers import TimedRotatingFileHandler

# Setup logger for GPS data
def setup_logger():
    logger = logging.getLogger('GPSLogger')
    handler = TimedRotatingFileHandler('gps_data.log', when="midnight", interval=1)
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

gps_logger = setup_logger()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("gps/topic")

def on_message(client, userdata, msg):
    gps_data = msg.payload.decode()
    print("GPS Data Received: " + gps_data)
    gps_logger.info(gps_data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60) 
