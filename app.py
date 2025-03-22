from flask import Flask, request, jsonify, render_template, abort
from dotenv import load_dotenv
import os
import lirc

app = Flask(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY", "defaultsecret")

# Available commands
AVAILABLE_COMMANDS = [
    "power_on", "power_off", "white_dimmer", "4h", "8h", "multi", "red",
    "green", "purple", "orange", "light_green", "blue", "yellow",
    "light_blue", "violet", "light_yellow", "teal", "pink"
]

def send_lirc_command(remote, command):
    client = lirc.Client()
    client.send_once(remote, command)
    client.close()

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

    try:
        send_lirc_command("ledlights", command)
        return jsonify({"status": f"Command '{command}' sent successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
