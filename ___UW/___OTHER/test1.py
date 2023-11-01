import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QDoubleSpinBox, QLabel, QSlider
from PyQt5.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PID Output Check")

        self.input_spinbox = QDoubleSpinBox()
        self.input_spinbox.setRange(0, 100)
        self.input_spinbox.setSingleStep(0.1)
        self.input_spinbox.setValue(0)
        self.input_spinbox.setDecimals(1)

        self.input_slider = QSlider(Qt.Horizontal)
        self.input_slider.setRange(0, 100)
        self.input_slider.setSingleStep(1)
        self.input_slider.setValue(0)
        self.input_slider.valueChanged.connect(self.update_input_spinbox)

        self.button_enter = QPushButton("Enter")
        self.button_enter.clicked.connect(self.analyze_diff)

        self.output_label = QLabel("Output Value: ")

        layout = QVBoxLayout()
        layout.addWidget(self.input_spinbox)
        layout.addWidget(self.input_slider)
        layout.addWidget(self.button_enter)
        layout.addWidget(self.output_label)
        self.setLayout(layout)

        self.last_error = 0
        self.integral = 0

    def update_input_spinbox(self, value):
        self.input_spinbox.setValue(value)

    def analyze_diff(self):
        target = 0
        input_value = self.input_spinbox.value()

        Kp = 0.2
        Ki = 0.3
        Kd = 0.5
        

        error =  target - input_value
        self.integral += error
        derivative = error - self.last_error

        output = (Kp * error) + (Ki * self.integral) + (Kd * derivative)

        self.last_error = error

        self.output_label.setText("Output Value: " + str(output))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
