import threading
import json
import signal
from flask import Flask, jsonify, request
from flask_cors import CORS
from lib.MIRRealTimeFeatureExtractor import RealTimeFileFeatureExtractor
from lib.utils.debug_utils import save_json, log_message

# Flask app
app = Flask(__name__)
CORS(app)

feature_extractor = RealTimeFileFeatureExtractor("test_track_0.wav")

# Data Storage
zcr_values = []
dom_freq_values = []

# Start the audio stream in a separate thread
def start_audio_stream():
    feature_extractor.start_stream()


@app.route("/get_zcr/<int:index>", methods=["GET"])
def get_zcr(index):
    zcr = feature_extractor.get_zcr_at_index(index)
    if zcr is not None:
        zcr_values.append({"index": index, "zcr": zcr})
        save_json(zcr_values, "zcr_values.json")  # Save to file
        return jsonify({"zcr": zcr})
    return jsonify({"error": "Index out of range"}), 404


@app.route("/get_dom_freq/<int:index>", methods=["GET"])
def get_dom_freq(index):
    dom_freq = feature_extractor.get_dom_freq_at_index(index)
    if dom_freq is not None:
        dom_freq_values.append({"index": index, "freq": dom_freq})  # Store correct index
        save_json(dom_freq_values, "dom_freq_values.json")  # Save to file
        return jsonify({"freq": dom_freq, "index": index})
    return jsonify({"error": "Index out of range"}), 404



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
    # Initialize JSON files to overwrite old data
    save_json([], "zcr_values.json")
    save_json([], "dom_freq_values.json")

    # Start audio stream in a background thread
    audio_thread = threading.Thread(target=start_audio_stream, daemon=True)
    audio_thread.start()

    # Run the Flask server
    try:
        app.run(host="127.0.0.1", port=5050)
    except Exception as e:
        print(f"Error occurred: {e}")
        handle_exit(None, None)