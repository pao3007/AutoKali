import pythoncom
from PyQt5.QtCore import QThread, pyqtSignal
from definitions import check_usb, check_function_gen_connected
from SettingsParams import MySettings


class ThreadCheckDevicesConnected(QThread):
    all_connected = pyqtSignal(bool, bool, bool, bool, bool)

    def __init__(self, opt_dev_vendor, ref_dev_vendor, my_settings: MySettings):
        super().__init__()
        self.termination = False
        self.opt_dev_vendor = opt_dev_vendor
        self.ref_dev_vendor = ref_dev_vendor
        self.my_settings = my_settings

    def run(self):
        pythoncom.CoInitialize()
        opt = False
        ref = False
        gen = False
        gen_error = False
        i = 9
        while not self.termination:
            i += 1
            if not (i % 10):
                opt, ref = check_usb(self.opt_dev_vendor, self.ref_dev_vendor)
                gen, gen_error = check_function_gen_connected(self.my_settings.generator_id, True)
                self.all_connected.emit(opt, ref, gen, gen_error, True)
                i = 0
            else:
                self.all_connected.emit(opt, ref, gen, gen_error, False)
            QThread.msleep(50)
