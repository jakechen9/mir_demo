import numpy as np
import librosa.feature
import sounddevice as sd


class FeatureExtractor:
    def __init__(self, filename, sr=44100, block_size=1024, scale=0.8):
        self.filename = filename
        self.sr = sr
        self.block_size = block_size
        self.scale = scale
        self.zcr_values = []
        self.audio, _ = librosa.load(filename, sr=sr, mono=True)
        self.audio *= scale  # Scale the audio signal

    def calculate_zcr(self):
        num_blocks = len(self.audio) // self.block_size
        for i in range(num_blocks):
            frame = self.audio[i * self.block_size: (i + 1) * self.block_size]
            zcr = librosa.feature.zero_crossing_rate(frame, frame_length=len(frame)).mean()
            self.zcr_values.append(zcr)
            sd.sleep(int(self.block_size / self.sr * 1000))  # Simulate real-time delay

    def get_zcr_at_index(self, index):
        if index < len(self.zcr_values):
            return self.zcr_values[index]
        return None

    def play_audio(self):
        sd.play(self.audio, samplerate=self.sr)
