import librosa.feature
import numpy as np
import pyaudio
import time
import threading
import queue

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
        self.dom_freq_values = []
        self.stop_event = threading.Event()  # Event to signal thread termination
        self.frame_queue = queue.Queue()  # Queue for frames to be processed

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
        # Start the background thread for feature extraction
        self.processing_thread = threading.Thread(target=self.process_features, daemon=True)
        self.processing_thread.start()

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
        # Send the frame to the processing queue
        self.frame_queue.put(frame)

        return frame.astype(np.float32).tobytes(), pyaudio.paContinue

    def process_features(self):
        """
        Background thread function to compute features asynchronously.
        """
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)  # Get a frame from the queue

                # Compute ZCR
                zcr = librosa.feature.zero_crossing_rate(frame, frame_length=len(frame), hop_length=len(frame)).mean()
                self.zcr_values.append(zcr)

                # Compute STFT
                stft_values = librosa.stft(frame, n_fft=2048, hop_length=len(frame), win_length=2048, window='hann')
                magnitude_spectrum = np.abs(stft_values).mean(axis=1)

                # Find the dominant frequency
                frequencies = librosa.fft_frequencies(sr=self.sr, n_fft=2048)  # Get frequency bin labels
                dominant_index = np.argmax(magnitude_spectrum)  # Find the peak frequency index
                dominant_frequency = frequencies[dominant_index]  # Get corresponding frequency value

                # Store the dominant pitch instead of full FFT spectrum
                self.dom_freq_values.append(dominant_frequency)

            except queue.Empty:
                continue  # If the queue is empty, keep looping

    def get_dom_freq_at_index(self, index):
        """
        Returns the Dominant Frequency value at a specific index.
        """
        if 0 <= index < len(self.dom_freq_values):
            return self.dom_freq_values[index]
        return None

    def get_zcr_at_index(self, index):
        """
        Returns the ZCR value at a specific index.
        """
        if 0 <= index < len(self.zcr_values):
            return self.zcr_values[index]
        return None

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
