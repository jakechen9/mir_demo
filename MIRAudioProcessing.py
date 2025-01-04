import threading
from flask import Flask, jsonify
from flask_cors import CORS
from lib.MIRFeatureExtractor import FeatureExtractor

# Flask app
app = Flask(__name__)
CORS(app)

# Create an AudioProcessor instance
feature_extractor = FeatureExtractor("test_track.wav")


# Start the ZCR calculation in a background thread
def start_zcr_calculation():
    feature_extractor.calculate_zcr()


@app.route("/get_zcr/<int:index>", methods=["GET"])
def get_zcr(index):
    zcr = feature_extractor.get_zcr_at_index(index)
    if zcr is not None:
        return jsonify({"zcr": zcr})
    else:
        return jsonify({"error": "Index out of range"}), 404


if __name__ == "__main__":
    # Start ZCR calculation in a separate thread
    threading.Thread(target=start_zcr_calculation, daemon=True).start()

    # Start audio playback in a separate thread
    threading.Thread(target=feature_extractor.play_audio, daemon=True).start()

    # Run the Flask server
    app.run(host="127.0.0.1", port=5050)
