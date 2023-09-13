from PyQt5.QtCore import QThread, pyqtSignal
from ThreadControlFuncGenStatements import ThreadControlFuncGenStatements


class ThreadProgressBar(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, argument: int, thcfgs: ThreadControlFuncGenStatements, auto_calib=None):
        super().__init__()
        self.duration = argument + 1
        self.thcfgs = thcfgs
        self.auto_calib = auto_calib

    def run(self):
        i = 1
        while (i < self.duration) and not self.thcfgs.get_emergency_stop() and not self.auto_calib.thread_check_sin_ref.isRunning():
            # print("PROGRESS BAR : " + str(self.thcfgs.get_emergency_stop()))
            QThread.msleep(1000)
            self.progress_signal.emit(i)
            i = i + 1
