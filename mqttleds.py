import paho.mqtt.client as mqtt
import queue
import threading
import lirc
from time import sleep
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Topics
MQTT_TOPICS = (
    ("gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:on/state", 0),
    ("gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:hue/state", 0)
)

# Command maps
on_off_command_map = {
    "1": ("ledlights", "power_on"),
    "0": ("ledlights", "power_off")
}

color_command_map = {
    2: ("ledlights", "white_dimmer"),
    3: ("ledlights", "white_dimmer"),
    4: ("ledlights", "red"),
    5: ("ledlights", "green"),
    6: ("ledlights", "purple"),
    7: ("ledlights", "orange"),
    8: ("ledlights", "light_green"),
    9: ("ledlights", "blue"),
    10: ("ledlights", "yellow"),
    11: ("ledlights", "light_blue"),
    12: ("ledlights", "violet"),
    13: ("ledlights", "light_yellow"),
    14: ("ledlights", "teal"),
    15: ("ledlights", "pink")
}

# Command queue
command_queue = queue.Queue()

# Sending lirc commands
def send_lirc_command(remote, command):
    try:
        print(f"Sending IR command: {remote} {command}")
        client = lirc.Client()
        client.send_once(remote, command)
        client.close()
    except Exception as e:
        print(f"Failed to send IR command: {e}")

# Worker thread
def process_commands():
    while True:
        remote_command = command_queue.get()
        if remote_command:
            remote, command = remote_command
            send_lirc_command(remote, command)
            sleep(0.3)
        command_queue.task_done()

# Start worker thread
threading.Thread(target=process_commands, daemon=True).start()

# MQTT Callbacks
def on_connect(client, userdata, flags, reasonCode, properties):
    print(f"Connected with reason code {reasonCode}")
    for topic, qos in MQTT_TOPICS:
        client.subscribe((topic, qos))
        print(f"Subscribed to {topic}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8').strip()
    topic = msg.topic
    print(f"Received message on {topic}: {payload}")

    if topic == "gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:on/state":
        if payload in on_off_command_map:
            command_queue.put(on_off_command_map[payload])
        else:
            print(f"Unknown ON/OFF command: {payload}")

    elif topic == "gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:hue/state":
        try:
            color_value = int(payload)
            if color_value in color_command_map:
                command_queue.put(color_command_map[color_value])
            else:
                print(f"Unhandled color value: {color_value}")
        except ValueError:
            print(f"Invalid color payload: {payload}")

# MQTT Setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Connect & loop
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
