import librosa.feature
import numpy as np
import pyaudio
import time
import threading


class RealTimeFileFeatureExtractor:
    """
    Real-time feature extractor for Zero Crossing Rate (ZCR) from a WAV file.
    """

    def __init__(self, filename, sr=44100, block_size=2048, scale=1.0):
        self.filename = filename
        self.sr = sr
        self.block_size = block_size
        self.scale = scale
        self.zcr_values = []
        self.spectral_cent = []
        self.rms_values = []
        self.stop_event = threading.Event()  # Event to signal thread termination

        # Load the audio file
        self.audio, _ = librosa.load(filename, sr=sr, mono=True)
        if scale != 1.0:
            self.audio *= scale  # Apply scaling if not 1.0

        # Initialize PyAudio stream for playback
        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_stream = self.pyaudio_instance.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sr,
            output=True,
            frames_per_buffer=2048,
            stream_callback=self.audio_callback
        )
        self.audio_index = 0

    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio callback function to process audio in real time.
        """
        start = self.audio_index
        end = start + frame_count

        if end >= len(self.audio):
            end = len(self.audio)
            data = self.audio[start:end].astype(np.float32).tobytes()
            self.audio_index = len(self.audio)
            return data, pyaudio.paComplete

        frame = self.audio[start:end]
        self.audio_index = end

        # Compute ZCR for the current frame
        zcr = librosa.feature.zero_crossing_rate(frame, frame_length=len(frame), hop_length=len(frame)).mean()
        self.zcr_values.append(zcr)

        spectral_centroid = librosa.feature.spectral_centroid(y=frame, n_fft=2048, sr=self.sr,
                                                              hop_length=len(frame)).mean()
        self.spectral_cent.append(spectral_centroid)

        rms = librosa.feature.rms(y=frame, frame_length=len(frame), hop_length=len(frame)).mean()
        self.rms_values.append(rms)

        return frame.astype(np.float32).tobytes(), pyaudio.paContinue

    def get_features_at_index(self, index):
        """
        Returns the ZCR value at a specific index.
        """
        features = {}

        if 0 <= index < len(self.zcr_values):
            features["zcr"] = float(self.zcr_values[index])
        if 0 <= index < len(self.rms_values):
            features["rms"] = float(self.rms_values[index])


        # if 0 <= index < len(self.zcr_values):
        #     return {
        #         "zcr": self.zcr_values[index],
        #         "rms": self.rms_values[index],
        #             }
        # return None
        return features if features else None

    def start_stream(self):
        """
        Starts the PyAudio stream for real-time audio processing.
        """
        self.audio_stream.start_stream()

        while self.audio_stream.is_active():
            if self.stop_event.is_set():
                break
            time.sleep(0.1)

        self.stop_stream()

    def stop_stream(self):
        """
        Stops the PyAudio stream and terminates PyAudio.
        """
        if self.audio_stream.is_active():
            self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.pyaudio_instance.terminate()
