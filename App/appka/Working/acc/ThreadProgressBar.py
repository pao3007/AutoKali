from PyQt5.QtCore import QThread, pyqtSignal
from acc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements


class ThreadProgressBar(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, argument: int, thcfgs: ThreadControlFuncGenStatements, auto_calib=None):
        super().__init__()
        self.duration = argument + 1
        self.thcfgs = thcfgs
        self.auto_calib = auto_calib

    def run(self):
        i = 1
        j = 0
        while (i < self.duration) and not self.thcfgs.get_emergency_stop() and not self.auto_calib.thread_check_sin_ref.isRunning():
            j += 1
            QThread.msleep(50)
            if j > 20:
                self.progress_signal.emit(i)
                i = i + 1
                j = 0
