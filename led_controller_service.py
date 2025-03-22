from flask import Flask, request, jsonify, render_template, abort
from dotenv import load_dotenv
import threading
import queue
import lirc
import os
import paho.mqtt.client as mqtt
from time import sleep

# ------------------------------
# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY", "defaultsecret")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# ------------------------------
# Command data & mappings

AVAILABLE_COMMANDS = [
    "power_on", "power_off", "white_dimmer", "4h", "8h", "multi", "red",
    "green", "purple", "orange", "light_green", "blue", "yellow",
    "light_blue", "violet", "light_yellow", "teal", "pink"
]

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

# ------------------------------
# Command queue & worker

command_queue = queue.Queue()

def send_lirc_command(remote, command):
    try:
        print(f"Sending IR command: {remote} {command}")
        client = lirc.Client()
        client.send_once(remote, command)
        client.close()
    except Exception as e:
        print(f"Failed to send IR command: {e}")

def process_commands():
    while True:
        remote_command = command_queue.get()
        if remote_command:
            remote, command = remote_command
            send_lirc_command(remote, command)
            sleep(0.3)  # prevent flooding lircd
        command_queue.task_done()

def start_worker_thread():
    threading.Thread(target=process_commands, daemon=True).start()

# ------------------------------
# Flask setup

app = Flask(__name__)

color_classes = {
    "white_dimmer": "bg-white hover:bg-white-200 text-black",
    "red": "bg-red-600 hover:bg-red-800",
    "green": "bg-green-600 hover:bg-green-800",
    "purple": "bg-purple-600 hover:bg-purple-800",
    "orange": "bg-orange-500 hover:bg-orange-700",
    "light_green": "bg-green-400 hover:bg-green-600",
    "blue": "bg-blue-600 hover:bg-blue-800",
    "yellow": "bg-yellow-400 hover:bg-yellow-600",
    "light_blue": "bg-sky-400 hover:bg-sky-600",
    "violet": "bg-violet-500 hover:bg-violet-700",
    "light_yellow": "bg-amber-300 hover:bg-amber-500",
    "teal": "bg-teal-500 hover:bg-teal-700",
    "pink": "bg-pink-500 hover:bg-pink-700"
}

@app.route("/")
def index():
    return render_template("index.html", commands=AVAILABLE_COMMANDS, api_key=API_KEY, color_classes=color_classes)

@app.route("/api/commands", methods=["GET"])
def get_commands():
    return jsonify({"commands": AVAILABLE_COMMANDS})

@app.route("/api/send", methods=["POST"])
def send_ir():
    data = request.json
    key = data.get("api_key")
    command = data.get("command")

    if key != API_KEY:
        abort(401, "Invalid API key")

    if command not in AVAILABLE_COMMANDS:
        return jsonify({"error": "Invalid command"}), 400

    # Queue command
    command_queue.put(("ledlights", command))
    return jsonify({"status": f"Command '{command}' queued."})

# ------------------------------
# MQTT setup

ON_STATE = "gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:on/state"
HUE_STATE = "gladys/device/mqtt:rgbleds/feature/mqtt:livingroom:rgbleds:hue/state"

MQTT_TOPICS = (
    (ON_STATE, 0),
    (HUE_STATE, 0)
)

def on_connect(client, userdata, flags, reasonCode, properties):
    print(f"Connected to MQTT with reason code {reasonCode}")
    for topic, qos in MQTT_TOPICS:
        client.subscribe((topic, qos))
        print(f"Subscribed to {topic}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8').strip()
    topic = msg.topic
    print(f"Received MQTT message on {topic}: {payload}")

    if topic == ON_STATE:
        if payload in on_off_command_map:
            command_queue.put(on_off_command_map[payload])
        else:
            print(f"Unknown ON/OFF command: {payload}")

    elif topic == HUE_STATE:
        try:
            color_value = int(payload)
            if color_value in color_command_map:
                command_queue.put(color_command_map[color_value])
            else:
                print(f"Unhandled color value: {color_value}")
        except ValueError:
            print(f"Invalid color payload: {payload}")

def start_mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()  # Start in background thread

# ------------------------------
# Main entry point for Gunicorn

# Create Flask app with no arguments passed to it
start_worker_thread()  # Start the command processing in the background
start_mqtt_client()    # Start MQTT listener in background

if __name__ == "__main__":
    app.debug = True  # Enable debug mode
    app.run(host="0.0.0.0", port=5000)
