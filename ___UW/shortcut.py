import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QShortcut, QKeySequence
from PyQt5.QtCore import Qt

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create a QAction for the action you want to trigger with the shortcut
        action = QAction('My Action', self)
        action.triggered.connect(self.myFunction)

        # Create a QShortcut and assign it to the desired key combination
        shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_A), self)
        shortcut.activated.connect(self.myFunction)

        # Add the action to the application's menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(action)

        self.setWindowTitle('Keyboard Shortcut Example')
        self.setGeometry(100, 100, 400, 300)

    def myFunction(self):
        print("Keyboard shortcut activated!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
