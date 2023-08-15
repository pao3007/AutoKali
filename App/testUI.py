from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from start_up import Ui_Setup
from autoCalibration import Ui_AutoCalibration
from settings import Ui_Settings

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Setup()
        self.ui.setupUi(self)

        self.ui.start_app.clicked.connect(self.open_settings_window)

    def open_settings_window(self):
        self.settings_window = MySettingsWindow()
        window.hide()
        self.settings_window.show()

class MySettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Settings()
        self.ui.setupUi(self)

if __name__ == "__main__":
    app = QApplication([])
    window = MyMainWindow()
    window.show()
    app.exec()
