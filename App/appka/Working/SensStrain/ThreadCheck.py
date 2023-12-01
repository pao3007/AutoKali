from PyQt5.QtCore import QThread, pyqtSignal

from definitions import check_usb, fetch_wavelengths_peak_logger
from MyStartUpWindow import MyStartUpWindow
from SensStrain.TMCStatements import TMCStatements


class ThreadCheck(QThread):
    benchtop_check = pyqtSignal(bool)
    opt_check = pyqtSignal(bool, list)
    update_check = pyqtSignal(bool)

    def __init__(self, my_start_window: MyStartUpWindow, tmcs: TMCStatements):
        super().__init__()
        self.vendor = my_start_window.ref_dev_vendor
        self.tmcs = tmcs
        self._termination = False
        self.thread_check_usb_bench = ThreadCheckBench(self)
        self.thread_check_usb_bench.start()

    def run(self):
        i = 0
        print("RUN")
        while not self._termination:
            i += 1
            res, wl = fetch_wavelengths_peak_logger(True)
            # if res == 200:
            #     self.opt_check.emit(True, wl)
            # elif res == 404:
            #     self.opt_check.emit(True, [-1])
            # elif res == -1:
            #     self.opt_check.emit(False, [-1])

            self.opt_check.emit(False if res == -1 else True, wl if res == 200 else [-1])
            self.msleep(250 if self.tmcs.disable_usb_check else 500)
            if i >= (4 if self.tmcs.disable_usb_check else 2):
                i = 0
                self.update_check.emit(True)

    @property
    def termination(self):
        return self._termination

    @termination.setter
    def termination(self, value):
        if isinstance(value, bool):
            self._termination = value
        else:
            raise ValueError("termination must be a boolean value")


class ThreadCheckBench(QThread):

    def __init__(self, parent: ThreadCheck):
        super().__init__()
        self.parent = parent
        self.vendor = self.parent.vendor

    def run(self):
        while not self.parent.termination:
            if not self.parent.tmcs.disable_usb_check:
                benchtop, _ = check_usb(self.vendor, self.vendor)
                self.parent.benchtop_check.emit(benchtop)
            self.msleep(1000)
