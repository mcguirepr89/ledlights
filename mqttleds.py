import paho.mqtt.client as mqtt
import subprocess
import queue
import threading
import time

# Config
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = (
    ("gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:on/state", 0),
    ("gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:hue/state", 0)
)

# Command maps
on_off_command_map = {
    "1": ["irsend", "SEND_ONCE", "ledlights", "power_on"],
    "0": ["irsend", "SEND_ONCE", "ledlights", "power_off"]
}

color_command_map = {
                2: ["irsend", "SEND_ONCE", "ledlights", "white_dimmer"],
                3: ["irsend", "SEND_ONCE", "ledlights", "white_dimmer"],
                4: ["irsend", "SEND_ONCE", "ledlights", "red"],
                5: ["irsend", "SEND_ONCE", "ledlights", "green"],
                6: ["irsend", "SEND_ONCE", "ledlights", "purple"],
                7: ["irsend", "SEND_ONCE", "ledlights", "orange"],
                8: ["irsend", "SEND_ONCE", "ledlights", "light_green"],
                9: ["irsend", "SEND_ONCE", "ledlights", "blue"],
                10: ["irsend", "SEND_ONCE", "ledlights", "yellow"],
                11: ["irsend", "SEND_ONCE", "ledlights", "light_blue"],
                12: ["irsend", "SEND_ONCE", "ledlights", "violet"],
                13: ["irsend", "SEND_ONCE", "ledlights", "light_yellow"],
                14: ["irsend", "SEND_ONCE", "ledlights", "teal"],
                15: ["irsend", "SEND_ONCE", "ledlights", "pink"]
}

# Command queue
command_queue = queue.Queue()

# Worker thread to process commands
def process_commands():
    while True:
        cmd = command_queue.get()
        if cmd:
            try:
                print(f"Executing command: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                time.sleep(0.3)  # Adjust delay as needed
            except subprocess.CalledProcessError as e:
                print(f"Failed to send IR command: {e}")
        command_queue.task_done()

# Start background worker thread
threading.Thread(target=process_commands, daemon=True).start()

# MQTT callbacks
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
            print(f"Invalid payload for color: {payload}")

# MQTT Client Setup
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("gladys", "mqttpassword")
client.on_connect = on_connect
client.on_message = on_message

# Connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
