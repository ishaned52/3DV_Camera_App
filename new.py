import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextBrowser, QVBoxLayout, QWidget

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("QTextBrowser Example")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a QVBoxLayout to add widgets to the central widget
        layout = QVBoxLayout(central_widget)

        # Create a QTextBrowser widget
        text_browser = QTextBrowser(self)
        text_browser.setOpenExternalLinks(True)  # Enable opening links in a web browser
        text_browser.setOpenExternalLinks(True)  # Enable opening links in a web browser
        layout.addWidget(text_browser)

        # Set some text content in the QTextBrowser
        text_browser.setPlainText("Hello, this is a QTextBrowser example.\nYou can display rich text here with HTML formatting.")

        # Show the main window
        self.show()

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
