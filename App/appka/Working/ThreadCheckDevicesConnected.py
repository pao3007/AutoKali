import pythoncom
from PyQt5.QtCore import QThread, pyqtSignal
from definitions import check_usb, check_function_gen_connected
from SensAcc.SettingsParams import MySettings
from nidaqmx import Task as nidaqmx_Task
from MyStartUpWindow import MyStartUpWindow


class ThreadCheckDevicesConnected(QThread):
    all_connected = pyqtSignal(bool, bool, bool, bool, bool, bool)
    all_connected_strain = pyqtSignal(bool, bool, bool)
    opt_connected = pyqtSignal(bool)

    def __init__(self, my_settings: MySettings, my_start_window: MyStartUpWindow, block=False):
        super().__init__()
        self.task_sin = None
        self.termination = False
        self._my_settings = my_settings
        self.block = block
        self.my_start_window = my_start_window

    def run(self):
        print("START CHECK")
        pythoncom.CoInitialize()
        opt = False
        ref = False
        gen = False
        gen_error = False
        bad_ref = False
        i = 9
        while not self.termination:
            if self.my_start_window.sens_type == "Accelerometer":
                if not self.block:
                    i += 1
                    if not (i % 10):
                        opt, ref = check_usb(self.my_start_window.opt_dev_vendor, self.my_start_window.ref_dev_vendor)
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
                        try:
                            gen, gen_error = check_function_gen_connected(self.my_settings.generator_id, True)
                            self.all_connected.emit(opt, ref, gen, gen_error, True, bad_ref)
                        except Exception:
                            pass
                        i = 0
                    else:
                        self.all_connected.emit(opt, ref, gen, gen_error, False, bad_ref)
                else:
                    try:
                        opt, _ = check_usb(self.my_start_window.opt_dev_vendor, self.my_start_window.ref_dev_vendor)
                        self.opt_connected.emit(opt)
                    except Exception:
                        pass
            elif self.my_start_window.sens_type == "Strain":
                i += 1
                try:
                    if not (i % 10):
                        opt, ref = check_usb(self.my_start_window.opt_dev_vendor, self.my_start_window.ref_dev_vendor)
                        self.all_connected_strain.emit(opt, ref, True)
                        i = 0
                    else:
                        self.all_connected_strain.emit(opt, ref, False)
                except Exception:
                    pass
            QThread.msleep(50)
        print("END CHECK")

    @property
    def my_settings(self):
        return self._my_settings

    @my_settings.setter
    def my_settings(self, value):
        if isinstance(value, MySettings):
            self._my_settings = value
        else:
            raise TypeError("my_settings must be an instance of MySettings class")
