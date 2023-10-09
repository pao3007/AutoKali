import numpy as np
import pythoncom
from PyQt5.QtCore import QThread, pyqtSignal
from nidaqmx import Task as nidaqmx_Task
from nidaqmx.constants import AcquisitionType, WAIT_INFINITELY
from SensAcc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from MyStartUpWindow import MyStartUpWindow
from SensAcc.ThreadSentinelCheckNewFile import ThreadSentinelCheckNewFile
from definitions import dominant_frequency, start_modbus, start_sentinel_d, kill_sentinel, check_usb, \
    check_function_gen_connected
from SensAcc.SettingsParams import MySettings
from pyModbusTCP.client import ModbusClient
from SensAcc.RollingAverager import RollingAverager


class AIOCheck(QThread):
    finished_signal = pyqtSignal()
    check_ready = pyqtSignal(int)
    out_value_ref = pyqtSignal(str)

    check_ready_opt = pyqtSignal(int)
    check_ready_gen = pyqtSignal(bool)
    check_gen_error = pyqtSignal(bool)
    out_value_opt = pyqtSignal(str)

    def __init__(self, thcfgs: ThreadControlFuncGenStatements, window: MyStartUpWindow, my_settings: MySettings,
                 server_ip, server_port, unit_id, address, number_of_samples, threshold):
        super().__init__()
        self.task_sin = None
        self.my_settings = my_settings
        self.disconnected = False
        self.sample_rate = 12800
        self.data = []
        self.last_peak = 0
        self.first_start = True
        self.noise = [0] * 12
        self.avg_noise = 0
        self.averager = RollingAverager(10)
        self.average = 0
        self.thcfgs = thcfgs
        self.window = window
        self.average2 = 0
        self.client = None
        self.thread_check_new_file = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.unit_id = unit_id
        self.address = address
        self.number_of_samples = number_of_samples
        self.threshold = threshold
        self.restart = False
        self.disconnect_count = 0
        self.do_action = False
        self.samples2 = np.empty(self.number_of_samples)
        self.samples1 = np.empty(self.number_of_samples)
        self.averager1 = RollingAverager(3)
        self.averager2 = RollingAverager(3)
        self.average1 = 0
        self.check = 0
        self.prevEmit = 0
        self.thcfgs.set_termination(False)

    def run(self):
        try:
            self.client = ModbusClient(host=self.server_ip, port=self.server_port, unit_id=self.unit_id)
            self.client.open()
            pythoncom.CoInitialize()
        except Exception as e:
            print(e)

        number_of_samples_per_channel = int(12800 / 6)
        print("START AIO CHECK")
        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        while not self.thcfgs.get_termination():
            print("LOOP 1")
            try:
                g = 9.80665
                self.task_sin = nidaqmx_Task(new_task_name='RefCheck')
                self.task_sin.ai_channels.add_ai_accel_chan(self.my_settings.ref_device_name + '/' +
                                                            self.my_settings.ref_channel,
                                                            sensitivity=self.my_settings.calib_reference_sensitivity * g)
                self.task_sin.timing.cfg_samp_clk_timing(self.sample_rate,
                                                         sample_mode=AcquisitionType.CONTINUOUS)
                self.task_sin.start()
            except Exception as e:
                print("TASK INIT:" + str(e))
                self.check_ready.emit(3)
                try:
                    self.task_sin.close()
                except Exception as e:
                    print(e)

                timeout = 0
                # 2 varianta
            while not self.thcfgs.get_termination():
                print("LOOP 2")
                try:
                    if self.window.calib_window.measure:
                        gen, _ = check_function_gen_connected(self.my_settings.generator_id)
                    else:
                        gen, gen_error = check_function_gen_connected(self.my_settings.generator_id, True)
                        self.check_gen_error.emit(gen_error)
                    self.check_ready_gen.emit(gen)
                    self.check_ready_opt.emit(self.check_if_ready())
                except Exception as e:
                    print("OPT: " + str(e))
                # print("REF 2")
                # print("CHECKING REF")
                try:
                    data = self.task_sin.read(number_of_samples_per_channel=-1)
                    max_g = np.max(np.abs(data))
                    # ready, amp = data_contains_sinus(data, 0.01)
                    peak = round(dominant_frequency(data, self.sample_rate), 2)
                    # print(str(peak) + " - " + str(max_g))
                    if not self.first_start:
                        if not self.thcfgs.get_start_sens_test():  # kontrola či je pripojený senzor
                            self.check_ready.emit(1)
                            timeout = 0
                            # self.average = self.averager.update(max_g)
                        else:
                            if ((self.my_settings.generator_sweep_stop_freq / 2 - (
                                    self.my_settings.generator_sweep_stop_freq / 2) / 20) <= peak <=
                                (self.my_settings.generator_sweep_stop_freq / 2 + (
                                        self.my_settings.generator_sweep_stop_freq / 2) / 20)) and (0.1 < max_g):
                                # print("True")
                                timeout += 1
                                if timeout >= 2:
                                    self.check_ready.emit(2)  # (2) je ok
                                    if timeout >= 2:
                                        timeout = 2
                            else:
                                if timeout > 0:
                                    timeout = 0
                                timeout -= 1
                                if timeout <= (-2):
                                    self.check_ready.emit(6)
                                    if timeout <= (-2):
                                        timeout = -2
                        self.last_peak = peak
                    self.first_start = False
                    if not self.thcfgs.get_start_sens_test():
                        out = str(np.round(np.mean(data), 5))
                    else:
                        out = str(np.round(max_g, 5))
                    out += " g"
                    self.out_value_ref.emit(out)
                except Exception as e:
                    print("REF MEASURE:" + str(e))
                    self.check_ready.emit(3)
                    try:
                        self.task_sin.close()
                    except Exception as e:
                        print(e)
                    break
            QThread.msleep(250)

    def check_if_ready(self):
        i = -1
        opt, _ = check_usb(self.window.opt_dev_vendor, self.window.ref_dev_vendor)
        if opt:
            self.do_action = True
        else:
            self.do_action = False

        if self.do_action:
            self.disconnect_count = 0
            while i < self.number_of_samples - 1 and not self.thcfgs.get_termination():
                regs1 = self.client.read_input_registers(self.address, 2)
                if regs1 is not None:
                    i += 1
                    # Assume the first register is the whole number and the second is the decimal part
                    sample = regs1[0] + regs1[1] / 1000  # Add them to form a floating point number
                    self.samples1[i] = sample
                    # print(sample)
                if self.my_settings.opt_channels == 2:
                    regs2 = self.client.read_input_registers(self.address + 2, 2)
                    if regs2 is not None:
                        # Assume the first register is the whole number and the second is the decimal part
                        sample = regs2[0] + regs2[1] / 1000  # Add them to form a floating point number
                        self.samples2[i] = sample
                        # print(sample)
                QThread.msleep(1)
            if self.thcfgs.get_termination():
                print("END OPT prevEmit")
                return self.prevEmit

            max_g_1 = np.max(self.samples1)
            mean_1 = np.mean(self.samples1)
            if not self.thcfgs.get_start_sens_test():
                out = str(round(mean_1, 3))
            else:
                out = str(round(max_g_1, 3))
            out += " nm\n"
            if self.my_settings.opt_channels == 2:
                max_g_2 = np.max(self.samples2)
                mean_2 = np.mean(self.samples2)
                if not self.thcfgs.get_start_sens_test():
                    out += str(round(mean_2, 3))
                else:
                    out += str(round(max_g_2, 3))
                out += " nm"

            self.out_value_opt.emit(out)

            if not self.first_start:
                if not self.thcfgs.get_start_sens_test():
                    self.average1 = self.averager1.update(mean_1)
                    if self.my_settings.opt_channels == 1:
                        self.prevEmit = int(not (np.any(self.samples1 == 0.0)))
                        return self.prevEmit
                    elif self.my_settings.opt_channels == 2:
                        self.average2 = self.averager2.update(mean_2)
                        dev = (np.abs(self.average1 - max_g_1) + np.abs(self.average2 - max_g_2)) / 2
                        # dev = (np.abs(self.average1 - max_g_1))
                        # print("avg : " + str(self.average1))
                        # print("MEAN : " + str(np.mean(self.samples1)))
                        # print("MAX : " + str(max_g_1))
                        # print("dev : " + str(dev))

                        if np.any(self.samples1 == 0.0) and np.any(self.samples2 == 0.0):
                            self.prevEmit = 0
                        elif np.any(self.samples1 == 0.0) or np.any(self.samples2 == 0.0):
                            self.prevEmit = 10
                        elif dev < 0.075:
                            self.prevEmit = 1
                        else:
                            self.prevEmit = 11

                        return self.prevEmit
                else:
                    if self.my_settings.opt_channels == 1:
                        dev = np.abs(self.average1 - max_g_1)
                        # print(dev)
                        if not np.any(self.samples1 == 0.0):
                            if dev > 0.001:
                                self.check += 1
                                if self.check >= 2:
                                    self.check = 0
                                    self.prevEmit = 5
                            else:
                                self.check -= 1
                                if self.check >= -2:
                                    self.check = 0
                                self.prevEmit = 4
                        else:
                            self.prevEmit = 0
                        return self.prevEmit
                    elif self.my_settings.opt_channels == 2:
                        dev = (np.abs(self.average1 - max_g_1) + np.abs(self.average2 - max_g_2)) / 2
                        print("dev : " + str(dev))
                        if ((not (np.any(self.samples1 == 0.0)) and int(not (np.any(self.samples2 == 0.0)))) and
                                (dev >= 0.1)):  # self.average1 - 0.075 > max_g_1 or self.average1 + 0.075 < max_g_1
                            self.check += 1
                            if self.check >= 2:
                                self.check = 0
                                self.prevEmit = 5
                                return self.prevEmit
                        else:
                            self.check = 0
                            self.prevEmit = 4
                            return self.prevEmit
            self.first_start = False
        else:
            self.check_ready_opt.emit(3)
            print("OPT. DEVICE IS DISCONNECTED \n")
            opt, _ = check_usb(self.window.opt_dev_vendor, self.window.ref_dev_vendor)
            while not opt:
                opt, _ = check_usb(self.window.opt_dev_vendor, self.window.ref_dev_vendor)
            self.restart_sentinel()
            self.client.open()

    def restart_sentinel(self):
        print("RESTART SENTINEL")
        kill_sentinel(True, True)
        QThread.msleep(100)
        start_sentinel_d(self.my_settings.opt_project, self.my_settings.folder_sentinel_D_folder, self.my_settings.subfolder_sentinel_project)
        self.thread_check_new_file = ThreadSentinelCheckNewFile(self.my_settings.folder_opt_export)
        self.thread_check_new_file.finished.connect(self.thread_check_new_file_finished)
        self.thread_check_new_file.start()
        self.thread_check_new_file.wait()

    def thread_check_new_file_finished(self):
        start_modbus(self.my_settings.folder_sentinel_modbus_folder,
                     self.my_settings.subfolder_sentinel_project,
                     self.my_settings.opt_project, self.my_settings.folder_opt_export,
                     self.my_settings.opt_channels,
                     self.thread_check_new_file.opt_sentinel_file_name)
