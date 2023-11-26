import pyttsx3
import sounddevice as sd
import wave
import numpy as np

class TextToSpeechPlayer:
    def __init__(self, device_name="CABLE Input (VB-Audio Virtual C"):
        self.device_index = self._find_device_index(device_name)
        self.engine = pyttsx3.init()

    def _find_device_index(self, device_name):
        """Find the index of the audio device with the specified name."""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if device_name in dev['name']:
                return i
        raise ValueError(f"Device '{device_name}' not found")

    def save_tts_to_wav(self, text, filename="output.wav"):
        """Convert text to speech and save it as a WAV file."""
        self.engine.save_to_file(text, filename)
        self.engine.runAndWait()

    def play_audio(self, filename, is_wav=True):
        """Play an audio file through the specified audio device."""
        try:
            if is_wav:
                self._play_wav(filename)
            else:
                # Extend this block for other audio formats if necessary
                raise NotImplementedError("Only WAV format is currently supported")
        except FileNotFoundError:
            print(f"File {filename} not found.")
        except Exception as e:
            print(f"Error playing {filename}: {e}")

    def _play_wav(self, filename):
        """Internal method to handle WAV file playback."""
        with wave.open(filename, 'rb') as wf:
            samplerate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.getnframes()
            audio_data = wf.readframes(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            if channels == 2:
                audio_array = np.reshape(audio_array, (frames, 2))

            sd.play(audio_array, samplerate=samplerate, device=self.device_index)
            sd.wait()