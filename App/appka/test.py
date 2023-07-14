import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton


class PopupWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Popup Window')
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        label = QLabel('This is a popup window.')
        layout.addWidget(label)

        button = QPushButton('Close')
        button.clicked.connect(self.close)
        layout.addWidget(button)

        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PopupWindow()
    window.exec_()
    sys.exit(app.exec_())
