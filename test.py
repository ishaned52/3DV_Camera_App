import sys
import numpy as np
import pyaudio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QThread, pyqtSignal

# Constants for audio stream
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class AudioStreamThread(QThread):
    # Signal to update volume level
    update_volume = pyqtSignal(int)

    def __init__(self, parent=None):
        super(AudioStreamThread, self).__init__(parent)
        self.pyaudio_instance = pyaudio.PyAudio()

    def run(self):
        # Open the audio stream
        stream = self.pyaudio_instance.open(format=FORMAT,
                                            channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            frames_per_buffer=CHUNK)

        while True:
            # Read audio stream
            data = np.fromstring(stream.read(CHUNK), dtype=np.int16)
            # Calculate volume
            volume = np.average(np.abs(data))
            # Emit signal with volume level
            self.update_volume.emit(int(volume))

    def stop(self):
        # Stop and close the audio stream
        stream.stop_stream()
        stream.close()
        self.pyaudio_instance.terminate()
        self.quit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the GUI layout
        layout = QVBoxLayout()
        self.volume_label = QLabel('Volume Level: 0')
        layout.addWidget(self.volume_label)
        self.setLayout(layout)

        # Set up the audio stream thread
        self.audio_thread = AudioStreamThread()
        self.audio_thread.update_volume.connect(self.update_volume_indicator)
        self.audio_thread.start()

    def update_volume_indicator(self, volume):
        self.volume_label.setText(f'Volume Level: {volume}')

    def closeEvent(self, event):
        self.audio_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
