from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from SensAcc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements


class ThreadProgressBar(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, argument: int, thcfgs: ThreadControlFuncGenStatements, auto_calib=None):
        super().__init__()
        self.timer = None
        self.duration = argument + 1
        self.thcfgs = thcfgs
        self.auto_calib = auto_calib
        self.i = 1

    def run(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.my_function)
        self.timer.start(1000)

    def my_function(self):
        self.progress_signal.emit(self.i)
        self.i += + 1
        # i = 1
        # j = 0
        # while (i < self.duration) and not self.thcfgs.get_emergency_stop() and not self.auto_calib.thread_check_sin_ref.isRunning():
        #     j += 1
        #     QThread.msleep(50)
        #     if j > 20:
        #         self.progress_signal.emit(i)
        #         i = i + 1
        #         j = 0
