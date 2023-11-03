import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser, QVBoxLayout, QWidget
import subprocess

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Device Name List in QTextBrowser")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a QVBoxLayout to add widgets to the central widget
        layout = QVBoxLayout(central_widget)

        # Create a QTextBrowser widget
        text_browser = QTextBrowser(self)
        layout.addWidget(text_browser)

        # Run the pactl command and capture its output
        output = subprocess.check_output(["pactl", "list", "short", "sources"], text=True)

        # Split the output into lines
        lines = output.splitlines()

        # Extract device names and store them in a list
        device_names = [line.split('\t')[1] for line in lines]

        # Display the device names in the QTextBrowser
        text_browser.setPlainText("\n".join(device_names))

        # Show the main window
        self.show()

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
