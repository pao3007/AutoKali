from PyQt5.QtCore import QThread, pyqtSignal
from acc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements


class ThreadSensorsCheckIfReady(QThread):
    check_ready = pyqtSignal(bool)

    def __init__(self,thcfgs: ThreadControlFuncGenStatements, auto_calib=None):
        super().__init__()
        self.termination = False
        self.auto_calib = auto_calib
        self.thcfgs = thcfgs

    def run(self):
        print("STARTING SENS CHECK THREAD LOOP")
        i = 4
        while not self.termination and not self.thcfgs.get_start_measuring():
            while (not self.termination and self.auto_calib.thread_check_sin_opt.isRunning() and
                   self.auto_calib.thread_check_sin_ref.isRunning()):
                i += 1
                if not (i % 5):
                    self.check_ready.emit(True)
                    i = 0
                else:
                    self.check_ready.emit(False)
                QThread.msleep(50)
                # print("CHECKING SENSORS")

            QThread.msleep(250)
        print("END SENS CHECKING")
