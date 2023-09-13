import sys
from PyQt5.QtWidgets import QMainWindow
from os import getcwd as os_getcwd

start_fold = os_getcwd()


def excepthook(exc_type, exc_value, exc_tb):
    from traceback import format_exception
    from definitions import kill_sentinel
    from os import chdir as os_chdir
    from datetime import datetime

    os_chdir(start_fold)
    tb = "".join(format_exception(exc_type, exc_value, exc_tb))
    current_time = datetime.now().time().strftime("%H:%M:%S.%f")
    today = datetime.today().strftime("%b-%d-%Y")
    with open("../error_log.txt", "a") as f:  # Open the file in append mode
        f.write(today)
        f.write(current_time)
        f.write(tb)  # Write the traceback to the file

    print("catched: ", tb)
    kill_sentinel(True, True)
    sys.exit(1)


# Install exception hook
sys.excepthook = excepthook


def read_version():
    from yaml import safe_load as yaml_safe_load
    try:
        with open('version_info.yaml', 'r') as f:
            data = yaml_safe_load(f)
            return float(data['version'])
    except FileNotFoundError:
        return 0.1


def write_version(new_version):
    from yaml import safe_dump as yaml_safe_dump
    with open('version.yaml', 'w') as f:
        yaml_safe_dump({'version': new_version}, f)


def check_for_updates(self):
    from PyQt5.QtWidgets import QMessageBox
    from requests import get as requests_get
    from json import loads as json_loads

    # url = "https://api.github.com/repos/your_username/your_repository/releases/latest"
    #
    # # Fetching latest release information
    # response = requests_get(url)
    # data = json_loads(response.text)
    #
    # latest_version = data["tag_name"]
    latest_version = 0.1

    # Compare versions
    if latest_version > read_version():
        reply = QMessageBox.question(self, "Update Available",
                                     f"New version {latest_version} is available. Do you want to update?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            return False
        else:
            return True
    return True


class Update(QMainWindow):

    def __init__(self):
        super().__init__()
        self.continue_app = None
        self.setWindowTitle("Update Checker")

    def get_continue_app(self):
        self.continue_app = check_for_updates(self)
        print(self.continue_app)
        return self.continue_app


if __name__ == "__main__":
    from PyQt5.QtWidgets import QSplashScreen, QApplication
    from PyQt5.QtCore import Qt, QCoreApplication
    from PyQt5.QtGui import QPixmap, QGuiApplication

    if hasattr(QCoreApplication, 'setAttribute'):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    if hasattr(QGuiApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication([])
    splash_pix = QPixmap('images/logo.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    from PyQt5.QtWidgets import QMainWindow
    if Update().get_continue_app():
        from MyStartUpWindow import MyStartUpWindow

        window = MyStartUpWindow(splash)
        app.exec()
    else:
        pass