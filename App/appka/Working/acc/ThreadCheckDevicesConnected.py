import pythoncom
from PyQt5.QtCore import QThread, pyqtSignal
from definitions import check_usb, check_function_gen_connected
from acc.SettingsParams import MySettings
from nidaqmx import Task as nidaqmx_Task


class ThreadCheckDevicesConnected(QThread):
    all_connected = pyqtSignal(bool, bool, bool, bool, bool, bool)
    opt_connected = pyqtSignal(bool)

    def __init__(self, opt_dev_vendor, ref_dev_vendor, my_settings: MySettings, block=False):
        super().__init__()
        self.task_sin = None
        self.termination = False
        self.opt_dev_vendor = opt_dev_vendor
        self.ref_dev_vendor = ref_dev_vendor
        self.my_settings = my_settings
        self.block = block

    def run(self):
        pythoncom.CoInitialize()
        opt = False
        ref = False
        gen = False
        gen_error = False
        bad_ref = False
        i = 9
        while not self.termination and not self.block:
            i += 1
            if not (i % 10):
                opt, ref = check_usb(self.opt_dev_vendor, self.ref_dev_vendor)
                if ref:
                    try:
                        self.task_sin = nidaqmx_Task(new_task_name='FirstCheckRef')
                        self.task_sin.ai_channels.add_ai_accel_chan(self.my_settings.ref_device_name + '/' +
                                                                    self.my_settings.ref_channel)
                        bad_ref = False
                    except Exception as e:
                        print(e)
                        bad_ref = True
                    finally:
                        self.task_sin.close()
                gen, gen_error = check_function_gen_connected(self.my_settings.generator_id, True)
                self.all_connected.emit(opt, ref, gen, gen_error, True, bad_ref)
                i = 0
            else:
                self.all_connected.emit(opt, ref, gen, gen_error, False, bad_ref)
            QThread.msleep(50)
        while not self.termination and self.block:
            opt, _ = check_usb(self.opt_dev_vendor, self.ref_dev_vendor)
            self.opt_connected.emit(opt)
            QThread.msleep(50)
