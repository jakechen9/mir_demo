import threading
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from lib.MIRRealTimeFeatureExtractor import RealTimeFileFeatureExtractor
import signal
import logging
import numpy as np
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # Suppress logs


feature_values = []

# Flask app
app = Flask(__name__)
CORS(app)

feature_extractor = RealTimeFileFeatureExtractor("test_track.wav")


# Start the audio stream in a separate thread
def start_audio_stream():
    feature_extractor.start_stream()


# @app.route("/get_zcr/<int:index>", methods=["GET"])
# def get_features(index):
#     features = feature_extractor.get_features_at_index(index)
#     if features is not None:
#         features = {k: float(v) if isinstance(v, np.float32) else v for k, v in features.items()}
#
#         # Append all feature values
#         feature_values.append({"index": index, **features})
#         # Save all feature values to JSON immediately
#         with open("features.json", "w") as json_file:
#             json.dump(feature_values, json_file)
#             print(f"Saved features at index {index} to features.json")
#
#         print(f"Features at index {index}: {features}")  # Print features live
#         return jsonify(features)
#     else:
#         return jsonify({"error": "Index out of range"}), 404


@app.route("/get_features/<int:index>", methods=["GET"])
def get_features(index):
    features = feature_extractor.get_features_at_index(index)

    if features is not None and len(features) > 0:  # Check if any feature is available
        # Convert all numpy.float32 values to Python float
        features = {k: float(v) if isinstance(v, (np.float32, np.float64)) else v for k, v in features.items()}

        # Append all feature values
        feature_values.append({"index": index, **features})
        # Save all feature values to JSON immediately
        with open("features.json", "w") as json_file:
            json.dump(feature_values, json_file)
            print(f"Saved features at index {index} to features.json")

        print(f"Features at index {index}: {features}")  # Print features live
        return jsonify(features)
    else:
        return jsonify({"error": f"Index {index} is out of range or no features available"}), 404



@app.route("/shutdown", methods=["POST"])
def shutdown():
    """
    Shutdown route to stop the audio stream and terminate the Flask server.
    """
    feature_extractor.stop_event.set()  # Signal the feature extractor to stop
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()  # Shutdown the Flask server
    return jsonify({"message": "Shutting down..."})


# Signal handler for graceful shutdown
def handle_exit(signal, frame):
    """
    Handle Ctrl+C or SIGTERM signals to cleanly stop the application.
    """
    print("Signal received, shutting down gracefully...")
    feature_extractor.stop_event.set()  # Signal threads to stop
    audio_thread.join()  # Wait for audio thread to complete
    feature_extractor.stop_stream()  # Clean up PyAudio resources
    print("Shutdown complete.")
    exit(0)


# Register signal handlers for SIGINT (Ctrl+C) and SIGTERM
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    # Initialize an empty JSON file to overwrite old data
    with open("features.json", "w") as json_file:
        json.dump([], json_file)  # Start with an empty JSON list

    # Start audio stream in a background thread
    audio_thread = threading.Thread(target=start_audio_stream, daemon=True)
    audio_thread.start()

    # Run the Flask server
    try:
        app.run(host="127.0.0.1", port=5050)
    except Exception as e:
        print(f"Error occurred: {e}")
        handle_exit(None, None)