import json

# Load configuration from JSON
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)

TEMP_DIR = config.get("TEMP_DIR", "./TEMP_DIR")
INPUT_DIR = config.get("INPUT_DIR", "./IN")
OUTPUT_DIR = config.get("OUTPUT_DIR", "./OUT")
IMSMANIFEST = config.get("IMSMANIFEST", "imsmanifest.xml")