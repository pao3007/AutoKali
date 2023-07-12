import time
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal


class CountThread(QThread):
    finished_signal = pyqtSignal()

    def run(self):
        time.sleep(10)  # Simulate long operation
        self.finished_signal.emit()  # Emit finished signal


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()
        self.button = QPushButton('Start Counting')
        self.button.clicked.connect(self.start_counting)

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def start_counting(self):
        self.button.setDisabled(True)  # Disable button

        # Create new QThread and connect its finished signal
        self.thread = CountThread()
        self.thread.finished_signal.connect(self.on_thread_finished)
        self.thread.start()

    def on_thread_finished(self):
        # Thread has finished, enable button
        self.button.setDisabled(False)


app = QApplication([])
window = MainWindow()
window.show()

app.exec_()
