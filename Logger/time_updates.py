import paho.mqtt.client as mqtt
import subprocess
import datetime

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("time/sync")

def on_message(client, userdata, msg):
    received_time = msg.payload.decode()
    try:
        # Set system time
        new_time = datetime.datetime.strptime(received_time, '%Y-%m-%d %H:%M:%S')
        subprocess.run(['sudo', 'date', '-s', new_time.strftime('%Y-%m-%d %H:%M:%S')], check=True)
        print(f"System time updated to: {received_time}")
    except Exception as e:
        print(f"Error setting time: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60) 
client.loop_forever()
