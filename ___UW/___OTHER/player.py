import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
import cv2

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(self.video_label)

        self.video_path = 'video.mp4'
        self.video_capture = cv2.VideoCapture(self.video_path)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.display_video)

    def start_video(self):
        self.timer.start(30)  # Update every 30 milliseconds

    def stop_video(self):
        self.timer.stop()

    def display_video(self):
        ret, frame = self.video_capture.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            pixmap = pixmap.scaled(self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio)
            self.video_label.setPixmap(pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.timer.isActive():
                self.stop_video()
            else:
                self.start_video()

    def closeEvent(self, event):
        self.video_capture.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayer()
    window.show()
    window.start_video()
    sys.exit(app.exec())
