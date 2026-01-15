import json
import logging

# Suppress Flask logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def save_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

def log_message(message):
    """Print debugging messages if needed."""
    print(message)  # Comment out this line to disable debugging logs
