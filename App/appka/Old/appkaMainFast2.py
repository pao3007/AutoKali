from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QPixmap, QGuiApplication

if __name__ == "__main__":
    if hasattr(QCoreApplication, 'setAttribute'):
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    if hasattr(QGuiApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication([])
    splash_pix = QPixmap('../Working/images/logo.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()

from matplotlib.pyplot import close as pyplot_close
from codecs import open as codecs_open
from configparser import ConfigParser
import pythoncom
import numpy as np
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QAction, QWidget
from PyQt5.QtCore import QFileInfo, QThread, pyqtSignal
from yaml import safe_load as yaml_safe_load, dump as yaml_dump, YAMLError
from nidaqmx import Task as nidaqmx_Task, system as nidaqmx_system
from nidaqmx.constants import AcquisitionType, WAIT_INFINITELY
from os import chdir as os_chdir, path as os_path, makedirs as os_makedirs, system as os_system, remove as os_remove, \
    listdir as os_listdir, rename as os_rename, getcwd as os_getcwd
from wmi import WMI as wmi_WMI
from scipy.fft import fft
from traceback import format_exception
from pyvisa import ResourceManager as pyvisa_ResourceManager
import sys
from start_up import Ui_Setup
from ImportWaveLengths import ImportWaveLengths
from xml.etree.ElementTree import parse as ET_parse
from re import search as re_search

start_fold = os_getcwd()


def excepthook(exc_type, exc_value, exc_tb):
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

# OK
def center_on_screen(self):
    screen_geo = QApplication.desktop().screenGeometry()
    window_geo = self.geometry()

    # Calculate the horizontal and vertical center position
    center_x = int((screen_geo.width() - window_geo.width()) / 2)
    center_y = int((screen_geo.height() - window_geo.height()) / 2)

    # Move the window to the calculated position
    self.move(center_x, center_y)

# OK
def scale_app(widget, scale_factor):
    # Check if it's a QWidget instance before accessing specific attributes
    if isinstance(widget, QWidget):

        # Adjust font size
        if hasattr(widget, 'font') and hasattr(widget, 'setFont'):
            font = widget.font()
            font.setPointSize(int(font.pointSize() * scale_factor))
            widget.setFont(font)

        # Adjust size for all widgets
        current_size = widget.size()
        widget.resize(int(current_size.width() * scale_factor), int(current_size.height() * scale_factor))

        # Adjust position for all widgets
        current_pos = widget.pos()
        widget.move(int(current_pos.x() * scale_factor), int(current_pos.y() * scale_factor))

    # Recursively scale child widgets or objects
    for child in widget.children():
        scale_app(child, scale_factor)

# ???
def channel_type_changed(index):
    window.opt_channels = int(index)
    kill_sentinel(False, True)
    start_sentinel_modbus(window.folder_sentinel_modbus_folder, window.folder_sentinel_D_folder, window.opt_project)

# OK
def start_sentinel_s(project):  # ! vybrat path to .exe a project

    sentinel_app = window.folder_sentinel_D_folder

    os_chdir(sentinel_app)
    os_system("start /min ClientApp_Dyn " + project)

# OK
def start_sentinel_modbus(modbus_path: str, sentinel_path: str, project: str):
    sentinel_app = modbus_path
    os_chdir(sentinel_app)

    config = ConfigParser()
    with codecs_open('settings.ini', 'r', encoding='utf-8-sig') as f:
        config.read_file(f)

    if window.opt_channels == 1:
        config.set('ranges', 'definition_file', f'{sentinel_path}/Sensors/{project}')
    elif window.opt_channels == 2:
        config.set('ranges', 'definition_file', f'{sentinel_path}/Sensors/{project}')

    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

    os_system("start /min Sentinel-Dynamic-Modbus")


def update_progress_bar(value):
    progress_sec = value
    if progress_sec < window.ref_measure_time:
        window.calib_window.ui.progressBar.setValue(int(100 * progress_sec / window.ref_measure_time))
    else:
        prog_finish = int(100 * progress_sec / window.ref_measure_time)
        if prog_finish < 100:
            window.calib_window.ui.progressBar.setValue(int(100 * progress_sec / window.ref_measure_time))
        else:
            window.calib_window.ui.progressBar.setValue(100)

# OK
def kill_sentinel(dyn: bool, mod: bool):
    if dyn:
        app_name = "ClientApp_Dyn"
        os_system(f'taskkill /F /IM {app_name}.exe')
    if mod:
        app_name = "Sentinel-Dynamic-Modbus"
        os_system(f'taskkill /F /IM {app_name}.exe')


# def data_contains_sinus(samples, threshold):
#     # Perform frequency domain analysis using Fourier Transform (FFT)
#     fft_values = np.fft.fft(samples)
#     amplitudes = np.abs(fft_values)
#     max_amplitude = np.max(amplitudes)
#
#     # Calculate the normalized amplitude of the dominant frequency
#     normalized_amplitude = max_amplitude / len(samples)
#
#     # Check if the waveform is sinusoidal based on the threshold
#     if normalized_amplitude >= threshold:
#         return True, normalized_amplitude
#     else:
#         return False, normalized_amplitude

# OK
def data_contains_sinus2(samples, sample_rate, peak_threshold):
    # Perform Fast Fourier Transform
    data = np.array(samples)
    yf = fft(data)
    xf = np.linspace(0.0, 1.0 / (2.0 / sample_rate), len(data) // 2)

    # Check if the signal forms a periodic waveform
    # If there is a peak in the frequency domain, we can say that there is a periodic signal
    peak_freqs = xf[np.abs(yf[:len(data) // 2]) > peak_threshold]

    return len(peak_freqs)

# OK
def start_modbus():
    kill_sentinel(True, False)
    start_sentinel_modbus(window.folder_sentinel_modbus_folder, window.folder_sentinel_D_folder, window.opt_project)
    QThread.msleep(100)

    os_chdir(window.folder_opt_export)

    if os_path.exists(window.calib_window.autoCalib.opt_sentinel_file_name + '.csv'):
        os_remove(window.calib_window.autoCalib.opt_sentinel_file_name + '.csv')

# OK
def check_usb(opt_vendor_ids, ref_vendor_ids):
    c = wmi_WMI()
    opt = False
    ref = False
    for usb in c.Win32_USBControllerDevice():
        try:
            device = usb.Dependent
            # The string to parse is like 'USB\\VID_045E&PID_07A5&MI_02\\7&37207CFF&0&0002'
            # VID is the vendor id
            device = device.DeviceID
            vid_start = device.find('VID_') + 4
            vid_end = device.find('&', vid_start)
            v_id = device[vid_start:vid_end]

            if v_id.upper() in [str(id1) for id1 in opt_vendor_ids]:
                opt = True
            if v_id.upper() in [str(id1) for id1 in ref_vendor_ids]:
                ref = True
            if opt and ref:
                break
        except Exception as e:
            pass
            return False, False
    return opt, ref


def check_function_gen_connected(generator_id):
    rm = pyvisa_ResourceManager()
    devices = rm.list_resources()

    if generator_id in devices:
        return True
    else:
        return False

# OK
def load_all_config_files(combobox, return_all_configs, config_file_path):
    combobox.blockSignals(True)
    combobox.clear()
    yaml_files = return_all_configs
    for yaml_file in yaml_files:
        combobox.addItem(os_path.basename(yaml_file))
    if not config_file_path is None:
        combobox.setCurrentText(QFileInfo(config_file_path).fileName())
    combobox.blockSignals(False)


def set_wavelengths(s_n: str, sentinel_file_path: str, project: str):
    iwl = ImportWaveLengths()
    wl = iwl.load_sylex_nominal_wavelength(objednavka_id=s_n)
    project_path = os_path.join(sentinel_file_path, f"Sensors/{project}")

    tree = ET_parse(project_path)
    root = tree.getroot()

    i = 0
    for peak_range in root.findall(".//PeakRangeDefinition"):
        print("PEAK")
        # Find RangeStart and RangeEnd elements
        range_start = peak_range.find("RangeStart")
        range_end = peak_range.find("RangeEnd")

        if range_start is not None and range_end is not None and i < len(wl):
            print("Change")
            # Modify their values
            range_start.text = str(float(wl[i] - 2))
            range_end.text = str(float(wl[i] + 2))
            i += 1
        else:
            return 0
    tree.write(project_path)
    return wl


#  settingWindows - kontrola zmien OK
class ThreadSettingsCheckNew(QThread):
    status = pyqtSignal()

    def __init__(self, nidaq_devices, resources, all_configs):
        super().__init__()
        self.termination = None
        self.nidaq_devices = nidaq_devices
        self.resources = resources
        self.all_configs = all_configs

    def run(self):
        while True:
            self.msleep(1000)

            system = nidaqmx_system.System.local()
            current_devices = system.devices.device_names

            rm = pyvisa_ResourceManager()
            current_resources = rm.list_resources()

            current_configs = window.return_all_configs()
            if not (set(self.nidaq_devices) == set(current_devices)) or \
                    not (set(self.resources) == set(current_resources)) or \
                    not (set(self.all_configs) == set(current_configs)):
                print("True")
                print(str(self.nidaq_devices) + " + " + str(current_devices))
                print(str(self.resources) + " + " + str(current_resources))
                print(str(self.all_configs) + " + " + str(current_configs))
                self.status.emit()


#  riadenie generátora funkcii
class ThreadControlFuncGen(QThread):
    connected_status = pyqtSignal(bool)
    step_status = pyqtSignal(str)

    def __init__(self, generator_id, generator_sweep_time, generator_sweep_start_freq, generator_sweep_stop_freq,
                 generator_sweep_type, generator_max_mvpp):
        super().__init__()
        self.generator_id = generator_id
        self.generator_sweep_time = generator_sweep_time
        self.generator_sweep_start_freq = generator_sweep_start_freq
        self.generator_sweep_stop_freq = generator_sweep_stop_freq
        self.generator_sweep_type = generator_sweep_type
        self.generator_max_vpp = generator_max_mvpp / 1000

    def run(self):
        try:
            rm = pyvisa_ResourceManager()
            self.step_status.emit("Starting the sensors test..." + self.generator_id)
            instrument = rm.open_resource(self.generator_id)
            self.msleep(25)
            instrument.write('OUTPut1:STATe OFF')

            instrument.write('SOURce1:FUNCtion SINusoid')
            instrument.write('SOURce1:FREQuency:MODE FIXed')
            instrument.write('SOURce1:FREQuency ' + str(self.generator_sweep_stop_freq / 2))
            instrument.write('SOURce1:VOLTage:LIMit:HIGH +' + str(self.generator_max_vpp))
            instrument.write('SOURce1:VOLTage:LIMit:STATe 0')
            instrument.write('SOURce1:VOLTage ' + str(self.generator_max_vpp / 5))
            instrument.write('TRIGger1:SOURce IMMediate')
            self.msleep(100)

            while not window.start_sens_test:
                if window.emergency_stop or not window.calib_window.sensor_gen_check:
                    window.emergency_stop = True
                    return
                self.msleep(25)

            if window.opt_channels == 2:
                self.step_status.emit("Testing sensors...\n\nPLEASE UNLOCK THE SENSOR!")
            else:
                self.step_status.emit("Testing sensors...")
            instrument.write('OUTPut1:STATe ON')
            i = 0
            while not window.end_sens_test:
                if window.emergency_stop or not window.calib_window.sensor_gen_check:
                    window.emergency_stop = True
                    return
                self.msleep(25)
                i += 1
                if i >= 20:
                    window.calib_window.ui.start_btn.setEnabled(True)  # moze robit problemy
            self.step_status.emit("Stopping the sensors testing...")
            instrument.write('OUTPut1:STATe OFF')

            kill_sentinel(False, True)
            start_sentinel_s(window.opt_project)

            while not window.start_measuring:
                if window.emergency_stop or not window.calib_window.sensor_gen_check:
                    window.emergency_stop = True
                    return
                self.msleep(25)
            instrument.write('SOURce1:FREQuency:MODE SWEep')
            instrument.write('SOURce1:FUNCtion ' + str(self.generator_sweep_type))
            instrument.write('SOURce1:FREQuency:STARt ' + str(self.generator_sweep_start_freq))
            instrument.write('SOURce1:FREQuency:STOP ' + str(self.generator_sweep_stop_freq))
            instrument.write('SOURce1:VOLTage ' + str(self.generator_max_vpp))
            instrument.write('SOURce1:SWEep:TIME ' + str(self.generator_sweep_time))
            instrument.write('TRIGger1:SOURce BUS')
            instrument.write('SOURce1:SWEep:SPACing LINear')  # LINear

            i = 0
            self.step_status.emit("Measuring central wavelength...")
            while i < 20:
                if window.emergency_stop or not window.calib_window.sensor_gen_check:
                    return
                self.msleep(25)
                i += 1
            instrument.write('OUTPut1:STATe ON')

            i = 0
            self.step_status.emit("Starting the measurement...")
            while i < 100:
                if window.emergency_stop or not window.calib_window.sensor_gen_check:
                    return
                self.msleep(25)
                i += 1
            instrument.write('TRIGger1')

            self.step_status.emit("Measuring sensors resposne for sweep function...")

            while not window.finished_measuring:
                if window.emergency_stop:
                    return
                if check_function_gen_connected(self.generator_id):
                    self.connected_status.emit(True)
                else:
                    window.emergency_stop = True
                    self.connected_status.emit(False)
                    return
                self.msleep(25)
        except Exception as e:
            print("GEN : " + str(e))


# vizualizácia priebehu
class ThreadProgressBar(QThread):
    progress_signal = pyqtSignal(int)

    def __init__(self, argument):
        super().__init__()
        self.duration = argument + 1

    def run(self):
        i = 1
        while i < self.duration and not window.emergency_stop:
            QThread.msleep(1000)
            self.progress_signal.emit(i)
            i = i + 1


#  kalibrácia - ref - zber dát
class ThreadRefSensDataCollection(QThread):
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.task = nidaqmx_Task()

    def run(self):
        self.start_ref_sens_data_collection()
        self.task.close()
        self.finished_signal.emit()

    def start_ref_sens_data_collection(self):
        from time import time as time_time
        from datetime import datetime

        window.calib_window.autoCalib.thread_check_sin_opt.terminate()
        window.calib_window.autoCalib.thread_check_sin_ref.terminate()

        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        self.task.ai_channels.add_ai_accel_chan(window.ref_device_name + '/' + window.ref_channel, sensitivity=1000)

        # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
        self.task.timing.cfg_samp_clk_timing(window.ref_sample_rate, sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=int(window.ref_number_of_samples))

        print("Start merania")
        current_time = datetime.now().time()
        window.calib_window.autoCalib.time_string = current_time.strftime("%H:%M:%S.%f")
        start_time = time_time()
        # spustenie získavania vzoriek
        self.task.start()

        # čítam získane vzorky
        data = self.task.read(number_of_samples_per_channel=window.ref_number_of_samples,
                              timeout=WAIT_INFINITELY)
        kill_sentinel(True, False)
        end_time = time_time()

        # stop
        # task.close()
        print("Stop merania")

        # dĺžka merania
        elapsed_time = (end_time - start_time) * 1000
        print(f"Cas trvania merania: {elapsed_time:.2f} ms")

        # ulozenie dát do txt súboru
        # self.save_data(data, elapsed_time)
        window.calib_window.autoCalib.save_data(data, elapsed_time)
        # self.refData = data
        start_sentinel_modbus(window.folder_sentinel_modbus_folder, window.folder_sentinel_D_folder, window.opt_project)
        window.finished_measuring = True


#  kontrola zapnutia sentinel-D
class ThreadSentinelCheckNewFile(QThread):
    finished_signal = pyqtSignal()

    def run(self):
        window.calib_window.autoCalib.check_new_files()
        self.finished_signal.emit()


#  kontrola stavu vsetkych senzorov
class ThreadSensorsCheckIfReady(QThread):
    check_ready = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.termination = False

    def run(self):
        print("STARTING SENS CHECK THREAD LOOP")
        while not self.termination:
            QThread.msleep(250)
            # print("CHECKING SENSORS")
            self.check_ready.emit()


#  kontrola optickeho senzora a generatora
class ThreadOptAndGenCheckIfReady(QThread):
    check_ready_opt = pyqtSignal(int)
    check_ready_gen = pyqtSignal(bool)
    from pyModbusTCP.client import ModbusClient
    from RollingAverager import RollingAverager

    def __init__(self, server_ip, server_port, unit_id, address, number_of_samples, threshold):
        super().__init__()
        self.client = None
        self.thread_check_new_file = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.unit_id = unit_id
        self.address = address
        self.number_of_samples = number_of_samples
        self.threshold = threshold
        self.termination = False
        self.restart = False
        self.disconnect_count = 0
        self.do_action = False
        self.samples2 = np.empty(self.number_of_samples)
        self.samples1 = np.empty(self.number_of_samples)
        self.first_start = True
        self.averager = self.RollingAverager(10)
        self.average = 0

    def run(self):
        self.client = self.ModbusClient(host=self.server_ip, port=self.server_port, unit_id=self.unit_id)
        self.client.open()
        pythoncom.CoInitialize()
        print("START OPT CHECK")
        while not self.termination:
            # print("CHECKING   OPT")
            try:
                self.check_ready_gen.emit(check_function_gen_connected(window.generator_id))
                self.check_ready_opt.emit(self.check_if_ready())
            except Exception as e:
                print("OPT: " + e)

    def check_if_ready(self):
        i = -1
        opt, _ = check_usb(window.opt_dev_vendor, window.ref_dev_vendor)
        if opt:
            self.do_action = True
        else:
            self.do_action = False

        if self.do_action:
            self.disconnect_count = 0
            while i < self.number_of_samples - 1:
                regs1 = self.client.read_input_registers(self.address, 2)
                if regs1 is not None:
                    i += 1
                    # Assume the first register is the whole number and the second is the decimal part
                    sample = regs1[0] + regs1[1] / 1000  # Add them to form a floating point number
                    self.samples1[i] = sample
                    # print(sample)
                if window.opt_channels == 2:
                    regs2 = self.client.read_input_registers(self.address + 2, 2)
                    if regs2 is not None:
                        # Assume the first register is the whole number and the second is the decimal part
                        sample = regs2[0] + regs2[1] / 1000  # Add them to form a floating point number
                        self.samples2[i] = sample
                        # print(sample)
                QThread.msleep(1)

            max = np.max(self.samples1)
            if not self.first_start:
                if not window.start_sens_test:
                    self.average = self.averager.update(max)
                    if window.opt_channels == 1:
                        return int(not (np.any(self.samples1 == 0.0)))
                    elif window.opt_channels == 2:
                        return int(not (np.any(self.samples1 == 0.0)) and int(not (np.any(self.samples2 == 0.0))))
                else:
                    if window.opt_channels == 1:
                        return int(not (np.any(self.samples1 == 0.0))) + 4
                    elif window.opt_channels == 2:
                        return (int(not (np.any(self.samples1 == 0.0)) and int(not (np.any(self.samples2 == 0.0))))
                                and (self.average-0.25 > max or self.average+0.25 < max)) + 4
            self.first_start = False

        else:
            self.check_ready_opt.emit(3)
            print("OPT. DEVICE IS DISCONNECTED \n")
            opt, _ = check_usb(window.opt_dev_vendor, window.ref_dev_vendor)
            while not opt:
                opt, _ = check_usb(window.opt_dev_vendor, window.ref_dev_vendor)
            self.restart_sentinel()
            self.client.open()

    def restart_sentinel(self):
        print("RESTART SENTINEL")
        kill_sentinel(True, True)
        QThread.msleep(100)
        start_sentinel_s(window.opt_project)
        self.thread_check_new_file = ThreadSentinelCheckNewFile()
        self.thread_check_new_file.finished.connect(start_modbus)
        self.thread_check_new_file.start()
        self.thread_check_new_file.wait()


def dominant_frequency(samples, sampling_rate):
    # Calculate the FFT and its magnitude
    fft_values = np.fft.fft(samples)
    magnitudes = np.abs(fft_values)

    # Find the frequency with the highest magnitude
    dominant_freq_index = np.argmax(magnitudes[1:]) + 1  # exclude the 0Hz component

    # Calculate the actual frequency in Hz
    freqs = np.fft.fftfreq(len(samples), 1 / sampling_rate)
    dominant_freq = freqs[dominant_freq_index]

    return abs(dominant_freq)


#  kontrola ref senzora
class ThreadRefCheckIfReady(QThread):
    finished_signal = pyqtSignal()
    check_ready = pyqtSignal(int)
    from RollingAverager import RollingAverager

    def __init__(self, device_name_and_channel):
        super().__init__()
        self.task_sin = None
        self.termination = False
        self.disconnected = False
        self.sample_rate = 12800
        self.deviceName_channel = device_name_and_channel
        self.data = []
        self.last_peak = 0
        self.first_start = True
        self.noise = [0] * 12
        self.avg_noise = 0
        self.averager = self.RollingAverager(10)
        self.average = 0

    def run(self):
        number_of_samples_per_channel = int(12800 / 6)
        print("Start ref sens sinus check")
        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        while not self.termination:
            # print("REF 1")
            try:
                self.task_sin = nidaqmx_Task()
                self.task_sin.ai_channels.add_ai_accel_chan(self.deviceName_channel, sensitivity=1000)
                self.task_sin.timing.cfg_samp_clk_timing(self.sample_rate,
                                                         sample_mode=AcquisitionType.CONTINUOUS)

                timeout = 0
                # 2 varianta
                while not self.termination:
                    # print("REF 2")
                    # print("CHECKING REF")
                    data = self.task_sin.read(number_of_samples_per_channel=number_of_samples_per_channel,
                                              timeout=WAIT_INFINITELY)
                    max_g = np.max(np.abs(data))
                    # ready, amp = data_contains_sinus(data, 0.01)
                    peak = round(dominant_frequency(data, self.sample_rate), 2)
                    # print(str(peak) + " - " + str(max_g))
                    if not self.first_start:
                        if not window.start_sens_test:  # kontrola či je pripojený senzor
                            self.check_ready.emit(1)
                            timeout = 0
                            self.average = self.averager.update(max_g)
                        else:
                            if ((window.generator_sweep_stop_freq / 2 - (
                                    window.generator_sweep_stop_freq / 2) / 20) <= peak <=
                                (window.generator_sweep_stop_freq / 2 + (
                                        window.generator_sweep_stop_freq / 2) / 20)) and peak == \
                                    self.last_peak and (2*self.average < max_g):
                                # print("True")
                                timeout += 1
                                if timeout >= 20:
                                    self.check_ready.emit(2)  # (2) je ok
                                    if timeout >= 20:
                                        timeout = 20
                            else:
                                if timeout > 0:
                                    timeout = 0
                                timeout -= 1
                                if timeout <= (-5):
                                    self.check_ready.emit(6)
                                    if timeout <= (-5):
                                        timeout = -5
                        self.last_peak = peak
                    self.first_start = False
                self.task_sin.close()
                break
            except Exception as e:
                print("REF CHECK:" + str(e))
                self.check_ready.emit(3)
                self.task_sin.close()

            QThread.msleep(333)



#  kontrola USB zariadení
class ThreadCheckDevicesConnected(QThread):
    all_connected = pyqtSignal(bool, bool, bool)

    def __init__(self, opt_dev_vendor, ref_dev_vendor):
        super().__init__()
        self.termination = False
        self.opt_dev_vendor = opt_dev_vendor
        self.ref_dev_vendor = ref_dev_vendor

    def run(self):
        pythoncom.CoInitialize()
        while not self.termination:
            opt, ref = check_usb(self.opt_dev_vendor, self.ref_dev_vendor)
            gen = check_function_gen_connected(window.generator_id)
            # ref = True

            self.all_connected.emit(opt, ref, gen)
            if opt and ref and gen:
                QThread.msleep(500)
            else:
                QThread.msleep(200)


#  úvodne okno
class MyStartUpWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.window_scale_delta = 1
        self.window_scale = 1
        self.calib_optical_sens_tolerance = None
        self.end_sens_test = False
        self.start_sens_test = False
        self.start_measuring = False
        self.finished_measuring = False
        self.emergency_stop = False
        self.yaml_devices_vendor = 'devices_vendor_ids.yaml'
        self.calib_phase_mark = None
        self.calib_angle_set_freq = None
        self.calib_r_flatness = None
        self.calib_l_flatness = None
        self.opt_dev_vendor = None
        self.ref_dev_vendor = None
        self.opt_first_start = True
        self.calib_window = None
        self.settings_window = None
        self.S_N = None
        self.folder_sentinel_S_folder = None
        self.folder_sentinel_D_folder = None
        self.folder_calibration_export = None
        self.folder_opt_export_raw = None
        self.folder_opt_export = None
        self.folder_ref_export_raw = None
        self.folder_ref_export = None
        self.folder_main = None
        self.calib_reference_sensitivity = None
        self.calib_do_spectrum = None
        self.calib_downsample = None
        self.calib_plot = None
        self.calib_filter_data = None
        self.calib_optical_sensitivity = None
        self.calib_gain_mark = None
        self.opt_project = None
        self.opt_sampling_rate = None
        self.opt_channels = None
        self.ref_sample_rate = None
        self.ref_number_of_samples = None
        self.ref_measure_time = None
        self.current_conf = None
        self.ref_device_name = None
        self.ref_channel = None
        self.opt_sensor_type = "Accelerometer"
        self.ref_connected = False

        self.generator_id = None
        self.generator_sweep_time = None
        self.generator_sweep_start_freq = None
        self.generator_sweep_stop_freq = None
        self.generator_sweep_type = None
        self.generator_max_mvpp = None

        self.starting_folder = os_getcwd()
        documents_path = os_path.expanduser('~/Documents')
        main_folder_name = 'Sylex_sensors_export'
        subfolder1a_name = 'reference'
        subfolder2a_name = 'optical'
        subfolder1b_name = 'reference_raw'
        subfolder2b_name = 'optical_raw'
        calibration_data_folder_name = 'calibration'
        config_folder_name = 'x_configs'

        self.folder_sentinel_modbus_folder = r"C:\Users\PC\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_Modbus_v1_0_7"
        self.main_folder_path = os_path.join(documents_path, main_folder_name)
        self.subfolderRef_path = os_path.join(self.main_folder_path, subfolder1a_name)
        self.subfolderOpt_path = os_path.join(self.main_folder_path, subfolder2a_name)
        self.subfolderRefRaw_path = os_path.join(self.main_folder_path, subfolder1b_name)
        self.subfolderOptRaw_path = os_path.join(self.main_folder_path, subfolder2b_name)
        self.subfolderCalibrationData = os_path.join(self.main_folder_path, calibration_data_folder_name)
        self.subfolderConfig_path = os_path.join(self.main_folder_path, config_folder_name)
        self.create_folders()

        self.def_config = {
            'current': True,
            'ref_device': {
                'channel': None,
                'name': None,
            },
            'ref_measurement': {
                'number_of_samples_per_channel': 320000,
                'sample_rate': 12800,
                'measure_time': 25
            },
            'opt_measurement': {
                'sensor_type': None,
                'sampling_rate': 800,
                'project': None,
                'channels': 1,
            },
            'calibration': {
                'gain_mark': 150,
                'optical_sensitivity': 0,
                'optical_sens_tolerance': 0,
                'filter_data': 'high-pass',
                'plot': 0,
                'downsample': 1,
                'do_spectrum': 1,
                'reference_sensitivity': 1,
                'l_flatness': 10,
                'r_flatness': 100,
                'angle_set_freq': 10,
                'phase_mark': 300,
            },
            'save_data': {
                'main_folder': self.main_folder_path,
                'ref_export': self.subfolderRef_path,
                'ref_export_raw': self.subfolderRefRaw_path,
                'opt_export': self.subfolderOpt_path,
                'opt_export_raw': self.subfolderOptRaw_path,
                'calibration_export': self.subfolderCalibrationData,
                'sentinel_D_folder': None,
                'sentinel_S_folder': None,
                'S_N': 'measured_data.csv'
            },
            'function_generator': {
                'generator_id': 'TCPIP0::10.88.5.166::inst0::INSTR',
                'generator_sweep_time': 0,
                'generator_sweep_start_freq': 0,
                'generator_sweep_stop_freq': 0,
                'generator_sweep_type': 'SINusoid',
                'generator_max_vpp': 0,
            }
        }

        self.config = None
        self.config_contains_none = True

        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        # connect btn
        self.ui.open_settings_btn.clicked.connect(self.open_settings_window)
        self.ui.start_app.clicked.connect(self.start_calib_app)
        # connect comboBox
        self.ui.sens_type_comboBox.currentTextChanged.connect(self.sens_type_combobox_changed)
        self.ui.ref_channel_comboBox.currentTextChanged.connect(self.ref_channel_combobox_changed)
        self.ui.ref_device_comboBox.currentTextChanged.connect(self.ref_device_combobox_changed)
        self.ui.opt_config_combobox.currentTextChanged.connect(self.config_combobox_changed)

        # buttons
        self.ui.start_app.setEnabled(False)

        # labels
        self.ui.status_opt_label.setText("Optical device")
        self.ui.status_opt_label.setStyleSheet("color: black;")
        self.ui.status_ref_label.setText("Reference device")
        self.ui.status_ref_label.setStyleSheet("color: black;")
        self.ui.null_detect_label.setStyleSheet("color: red;")
        self.ui.null_detect_label.setHidden(True)

        #  graphics
        self.ui.logo_label.setPixmap(QPixmap("../Working/images/logo.png"))

        scale_app(self, self.window_scale)

        self.config_file_path = self.check_config_if_selected()
        self.setup_config()
        self.load_usb_dev_vendors()

        self.thread_check_usb_devices = ThreadCheckDevicesConnected(self.opt_dev_vendor, self.ref_dev_vendor)
        self.thread_check_usb_devices.all_connected.connect(self.all_dev_connected_signal)
        self.thread_check_usb_devices.start()
        self.setWindowIcon(QIcon('../Working/images/logo_icon.png'))
        splash.hide()
        self.show()

    def config_combobox_changed(self, text):
        self.config_file_path = os_path.join(window.subfolderConfig_path, text)
        with open(self.config_file_path, 'r') as file:
            config_check = yaml_safe_load(file)
        if self.config['opt_measurement']['sensor_type'] == config_check['opt_measurement']['sensor_type']:
            self.current_conf = False
            self.save_config_file(False)

        self.setup_config()
        self.current_conf = True
        self.save_config_file(True)

    def load_usb_dev_vendors(self):
        config_file_path = os_path.join(self.starting_folder, self.yaml_devices_vendor)
        with open(config_file_path, 'r') as file:
            data = yaml_safe_load(file)

        self.opt_dev_vendor = data['optical']
        self.ref_dev_vendor = data['reference']

    def showEvent(self, event):
        scale_app(self, self.window_scale_delta)
        self.window_scale_delta = 1
        center_on_screen(self)
        self.check_devices_load_comboboxes()

    def channel_type_changed(self, index):
        self.opt_channels = int(index)

    def create_folders(self):
        if not os_path.exists(self.main_folder_path):
            # Create the main folder
            os_makedirs(self.main_folder_path)

        # Create the subfolders inside the main folder
        os_makedirs(self.subfolderRef_path, exist_ok=True)
        os_makedirs(self.subfolderOpt_path, exist_ok=True)
        os_makedirs(self.subfolderRefRaw_path, exist_ok=True)
        os_makedirs(self.subfolderOptRaw_path, exist_ok=True)
        os_makedirs(self.subfolderCalibrationData, exist_ok=True)
        os_makedirs(self.subfolderConfig_path, exist_ok=True)

    def check_if_none(self):
        def traverse(data):
            if data is None or data == '':
                return True
            if isinstance(data, dict):
                return any(traverse(value) for value in data.values())
            if isinstance(data, list):
                return any(traverse(item) for item in data)
            return False

        try:
            self.config_contains_none = traverse(self.config)
        except YAMLError as e:
            print(f"Error parsing YAML: {e}")
            self.config_contains_none = True

    def all_dev_connected_signal(self, opt_connected, ref_connected, gen_connected):
        if self.config_contains_none:
            self.ui.null_detect_label.setHidden(False)
            self.ui.null_detect_label.setEnabled(not self.ui.null_detect_label.isEnabled())
            self.ui.null_detect_label.setStyleSheet(
                "color: red;" if self.ui.null_detect_label.isEnabled() else "color: black;")
            self.ui.start_app.setEnabled(False)
        elif window.opt_channels != 0:
            self.ui.null_detect_label.setHidden(True)
            if ref_connected and opt_connected and gen_connected and self.ui.start_app.text() == "START":
                self.ui.start_app.setEnabled(True)
        else:
            self.ui.start_app.setEnabled(False)

        for status, device_name, connected_flag in [
            (self.ui.status_ref_label, "Reference USB device", ref_connected),
            (self.ui.status_opt_label, "Optical USB device", opt_connected),
            (self.ui.status_gen_label, "Function generator", gen_connected)
        ]:
            status.setEnabled(not status.isEnabled())
            status.setText(f"{device_name} {'DISCONNECTED' if not connected_flag else 'CONNECTED'}")
            status.setStyleSheet(
                "color: red;" if not connected_flag and status.isEnabled() else "color: black;" if not connected_flag else "color: green;")

            if device_name == "Reference USB device" and not connected_flag and self.ref_connected:
                self.check_devices_load_comboboxes()
                self.ref_connected = False
            elif device_name == "Reference USB device" and connected_flag and not self.ref_connected:
                self.ref_connected = True
                self.check_devices_load_comboboxes()

    def sens_type_combobox_changed(self, text):
        self.opt_sensor_type = text
        self.config_file_path = self.check_config_if_selected()
        load_all_config_files(self.ui.opt_config_combobox, self.return_all_configs(), self.config_file_path)
        self.setup_config()

        # self.save_config_file(True)

    def ref_channel_combobox_changed(self, text):
        self.ref_channel = text
        self.save_config_file(True)

    def ref_device_combobox_changed(self, text):
        if text != "NOT DETECTED":
            self.ref_device_name = text
        self.save_config_file(True)

    def return_all_configs(self):
        from glob import glob
        yaml_files = glob(os_path.join(self.subfolderConfig_path, '*.yaml'))
        yaml_return = []
        for yaml_file in yaml_files:
            config_file_path = os_path.join(self.subfolderConfig_path, yaml_file)
            with open(config_file_path, 'r') as file:
                config = yaml_safe_load(file)
                if config['opt_measurement']['sensor_type'] == self.opt_sensor_type:
                    yaml_return.append(yaml_file)
        return yaml_return

    def check_config_if_selected(self):
        yaml_files = self.return_all_configs()
        for yaml_file in yaml_files:
            config_file_path = os_path.join(self.subfolderConfig_path, yaml_file)
            with open(config_file_path, 'r') as file:
                config = yaml_safe_load(file)
                if config['current']:
                    return config_file_path
        return None

    def setup_config(self):
        if self.config_file_path is not None and os_path.exists(self.config_file_path):
            self.load_config_file()
            self.check_devices_load_comboboxes()
        else:
            self.create_config_file()
            self.check_devices_load_comboboxes()

    def load_config_file(self):
        with open(self.config_file_path, 'r') as file:
            self.config = yaml_safe_load(file)

        self.current_conf = self.config['current']
        self.ref_channel = self.config['ref_device']['channel']
        self.ref_device_name = self.config['ref_device']['name']

        # self.ref_number_of_samples = int(self.config['ref_measurement']['number_of_samples_per_channel'])
        self.ref_sample_rate = int(self.config['ref_measurement']['sample_rate'])

        # self.opt_sensor_type = self.config['opt_measurement']['sensor_type']
        self.opt_sampling_rate = int(self.config['opt_measurement']['sampling_rate'])
        self.opt_project = self.config['opt_measurement']['project']
        self.opt_channels = int(self.config['opt_measurement']['channels'])

        self.calib_gain_mark = int(self.config['calibration']['gain_mark'])
        self.calib_optical_sensitivity = float(self.config['calibration']['optical_sensitivity'])
        self.calib_optical_sens_tolerance = float(self.config['calibration']['optical_sens_tolerance'])
        self.calib_filter_data = self.config['calibration']['filter_data']
        self.calib_plot = self.config['calibration']['plot']
        self.calib_downsample = int(self.config['calibration']['downsample'])
        self.calib_do_spectrum = int(self.config['calibration']['do_spectrum'])
        self.calib_reference_sensitivity = float(self.config['calibration']['reference_sensitivity'])
        self.calib_l_flatness = int(self.config['calibration']['l_flatness'])
        self.calib_r_flatness = int(self.config['calibration']['r_flatness'])
        self.calib_angle_set_freq = int(self.config['calibration']['angle_set_freq'])
        self.calib_phase_mark = int(self.config['calibration']['phase_mark'])

        self.folder_main = self.config['save_data']['main_folder']
        self.folder_ref_export = self.config['save_data']['ref_export']
        self.folder_ref_export_raw = self.config['save_data']['ref_export_raw']
        self.folder_opt_export = self.config['save_data']['opt_export']
        self.folder_opt_export_raw = self.config['save_data']['opt_export_raw']
        self.folder_calibration_export = self.config['save_data']['calibration_export']
        self.folder_sentinel_D_folder = self.config['save_data']['sentinel_D_folder']
        self.folder_sentinel_S_folder = self.config['save_data']['sentinel_S_folder']
        self.S_N = self.config['save_data']['S_N']

        self.generator_id = self.config['function_generator']['generator_id']
        self.generator_sweep_time = int(self.config['function_generator']['generator_sweep_time'])
        self.generator_sweep_start_freq = int(self.config['function_generator']['generator_sweep_start_freq'])
        self.generator_sweep_stop_freq = int(self.config['function_generator']['generator_sweep_stop_freq'])
        self.generator_sweep_type = self.config['function_generator']['generator_sweep_type']
        self.generator_max_mvpp = int(self.config['function_generator']['generator_max_vpp'])

        self.ref_measure_time = int(self.generator_sweep_time + 5)
        self.ref_number_of_samples = int(self.ref_measure_time * self.ref_sample_rate)

        self.check_if_none()

    def create_config_file(self):
        yaml_name = 'default_config.yaml'
        self.config_file_path = os_path.join(self.subfolderConfig_path, yaml_name)
        new_conf = self.def_config
        new_conf['opt_measurement']['sensor_type'] = self.opt_sensor_type
        with open(self.config_file_path, 'w') as file:
            yaml_dump(new_conf, file)

        self.load_config_file()

    def save_config_file(self, current_conf):
        self.config['current'] = current_conf
        self.config['ref_device']['channel'] = self.ref_channel
        self.config['ref_device']['name'] = self.ref_device_name

        self.config['ref_measurement']['number_of_samples_per_channel'] = self.ref_number_of_samples
        self.config['ref_measurement']['sample_rate'] = self.ref_sample_rate

        self.config['opt_measurement']['sensor_type'] = self.opt_sensor_type
        self.config['opt_measurement']['sampling_rate'] = self.opt_sampling_rate
        self.config['opt_measurement']['project'] = self.opt_project
        self.config['opt_measurement']['channels'] = self.opt_channels

        self.config['calibration']['gain_mark'] = self.calib_gain_mark
        self.config['calibration']['optical_sensitivity'] = self.calib_optical_sensitivity
        self.config['calibration']['optical_sens_tolerance'] = self.calib_optical_sens_tolerance
        self.config['calibration']['filter_data'] = self.calib_filter_data
        self.config['calibration']['plot'] = self.calib_plot
        self.config['calibration']['downsample'] = self.calib_downsample
        self.config['calibration']['do_spectrum'] = self.calib_do_spectrum
        self.config['calibration']['reference_sensitivity'] = self.calib_reference_sensitivity
        self.config['calibration']['l_flatness'] = self.calib_l_flatness
        self.config['calibration']['r_flatness'] = self.calib_r_flatness
        self.config['calibration']['angle_set_freq'] = self.calib_angle_set_freq
        self.config['calibration']['phase_mark'] = self.calib_phase_mark

        self.config['save_data']['main_folder'] = self.folder_main
        self.config['save_data']['ref_export'] = self.folder_ref_export
        self.config['save_data']['ref_export_raw'] = self.folder_ref_export_raw
        self.config['save_data']['opt_export'] = self.folder_opt_export
        self.config['save_data']['opt_export_raw'] = self.folder_opt_export_raw
        self.config['save_data']['calibration_export'] = self.folder_calibration_export
        self.config['save_data']['sentinel_D_folder'] = self.folder_sentinel_D_folder
        self.config['save_data']['sentinel_S_folder'] = self.folder_sentinel_S_folder

        self.config['function_generator']['generator_id'] = self.generator_id
        self.config['function_generator']['generator_sweep_time'] = self.generator_sweep_time
        self.config['function_generator']['generator_sweep_start_freq'] = self.generator_sweep_start_freq
        self.config['function_generator']['generator_sweep_stop_freq'] = self.generator_sweep_stop_freq
        self.config['function_generator']['generator_sweep_type'] = self.generator_sweep_type
        self.config['function_generator']['generator_max_vpp'] = self.generator_max_mvpp

        self.config['save_data']['S_N'] = self.S_N

        with open(self.config_file_path, 'w') as file:
            yaml_dump(self.config, file)

        self.check_if_none()

    def check_devices_load_comboboxes(self):
        self.ui.ref_device_comboBox.blockSignals(True)
        self.ui.ref_channel_comboBox.blockSignals(True)
        self.ui.sens_type_comboBox.blockSignals(True)
        self.ui.opt_config_combobox.blockSignals(True)

        self.ui.ref_device_comboBox.clear()
        self.ui.ref_channel_comboBox.clear()
        self.ui.sens_type_comboBox.clear()

        # load optical sensor types
        self.ui.sens_type_comboBox.addItem('Accelerometer')
        self.ui.sens_type_comboBox.addItem('Test')
        self.ui.sens_type_comboBox.setCurrentText(self.opt_sensor_type)

        # load ref sens devices
        system = nidaqmx_system.System.local()
        for device in system.devices:
            self.ui.ref_device_comboBox.addItem(f'{device.name}')
        if self.ref_device_name is not None and self.ui.ref_device_comboBox.count() != 0:
            self.ui.ref_device_comboBox.setCurrentText(self.ref_device_name)
        else:
            self.ui.ref_device_comboBox.addItem('NOT DETECTED')
            self.ui.ref_device_comboBox.setCurrentText("NOT DETECTED")

        # load ref sens channels
        self.ui.ref_channel_comboBox.addItem('ai0')
        self.ui.ref_channel_comboBox.addItem('ai1')
        self.ui.ref_channel_comboBox.addItem('ai2')
        print("Load comboBox ref channel\n")
        if self.ref_channel is not None:
            print("select channel : " + self.ref_channel)
            self.ui.ref_channel_comboBox.setCurrentText(self.ref_channel)

        load_all_config_files(self.ui.opt_config_combobox, self.return_all_configs(), self.config_file_path)

        self.ui.ref_device_comboBox.blockSignals(False)
        self.ui.ref_channel_comboBox.blockSignals(False)
        self.ui.sens_type_comboBox.blockSignals(False)
        self.ui.opt_config_combobox.blockSignals(False)

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(True)
        self.hide()
        self.settings_window.show()

    def start_calib_app(self):
        path_config = os_path.join(self.folder_sentinel_D_folder,"config.ini")
        config = ConfigParser()
        with codecs_open(path_config, 'r', encoding='utf-8-sig') as f:
            config.read_file(f)
        config.set('general', 'export_folder_path', self.folder_opt_export)
        with open(path_config, 'w') as configfile:
            config.write(configfile)

        self.ui.ref_device_comboBox.setEnabled(False)
        self.ui.opt_config_combobox.setEnabled(False)
        self.ui.ref_channel_comboBox.setEnabled(False)
        self.ui.sens_type_comboBox.setEnabled(False)
        self.ui.open_settings_btn.setEnabled(False)
        self.ui.menubar.setEnabled(False)
        self.ui.start_app.setText("STARTING")
        self.ui.start_app.setEnabled(False)
        self.thread_check_usb_devices.termination = True
        self.calib_window = MyMainWindow()
        self.calib_window.first_sentinel_start()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to exit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.thread_check_usb_devices.termination = True
            self.thread_check_usb_devices.wait()
            event.accept()
        else:
            event.ignore()


# nastavenia parametrov
class MySettingsWindow(QMainWindow):
    def __init__(self, start):
        super().__init__()
        self.all_configs = None
        self.resources = None
        from settings import Ui_Settings
        self.config_file_path = None
        self.nidaq_devices = None
        self.start = start
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.load_settings()
        self.config_file = None
        self.slider_value = window.window_scale

        # btns
        self.ui.save_btn.clicked.connect(self.save_settings)
        self.ui.cancel_btn.clicked.connect(self.load_settings)

        self.ui.main_folder_btn.clicked.connect(self.main_folder_path_select)
        self.ui.ref_exp_fold_btn.clicked.connect(self.ref_export_folder_path_select)
        self.ui.ref_export_fold_raw_btn.clicked.connect(self.ref_export_raw_folder_path_select)

        self.ui.opt_exp_fold_btn.clicked.connect(self.opt_export_folder_path_select)
        self.ui.opt_exp_fold_raw_btn.clicked.connect(self.opt_export_raw_folder_path_select)
        self.ui.opt_sentinel_fold_btn.clicked.connect(self.opt_sentinel_d_folder_path_select)
        self.ui.opt_sentinel_S_fold_btn.clicked.connect(self.opt_sentinel_s_folder_path_select)
        self.ui.opt_loaded_project_btn.clicked.connect(self.opt_sentinel_load_proj)

        self.ui.btn_ref_tab.clicked.connect(self.clicked_btn_reference)
        self.ui.btn_opt_tab.clicked.connect(self.clicked_btn_optical)
        self.ui.btn_calib_tab.clicked.connect(self.clicked_btn_calib)
        self.ui.btn_gen_tab.clicked.connect(self.clicked_btn_gen)

        self.ui.slider_win_scale.setRange(1, 5)
        self.ui.slider_win_scale.valueChanged.connect(self.slider_scale_changed)

        self.ui.logo_label.setPixmap(QPixmap("../Working/images/logo.png"))

        self.ui.calib_export_btn.clicked.connect(self.calib_export_folder_path_select)
        self.ui.save_as_btn.clicked.connect(self.save_as_settings)
        self.ui.select_config_file.currentTextChanged.connect(self.select_config_file_combobox_changed)
        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_gen.hide()

        self.btn_translate_dy = 8
        self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(), self.ui.btn_ref_tab.pos().y() + self.btn_translate_dy)
        self.ui.btn_ref_tab.setEnabled(False)
        self.thread_check_new = ThreadSettingsCheckNew(self.nidaq_devices, self.resources, self.all_configs)
        self.thread_check_new.status.connect(self.new_setting_enabled)
        self.thread_check_new.start()
        self.setWindowIcon(QIcon('../Working/images/logo_icon.png'))
        scale_app(self, window.window_scale)

    def slider_scale_get_real_value(self, value):
        def get_key_for_value(d, value):
            for k, v in d.items():
                if v == value:
                    return k
            return None

        # Mapping integer values of the slider to the desired float values
        mapping = {
            1: 1,
            2: 1.25,
            3: 1.5,
            4: 1.75,
            5: 2
        }
        return mapping[int(value)], get_key_for_value(mapping, value)

    def slider_scale_changed(self, value):
        self.slider_value, _ = self.slider_scale_get_real_value(value)
        self.ui.settings_scale2x_label.setText(str(self.slider_value) + "x")

    def move_btns_back(self):
        if not self.ui.btn_calib_tab.isEnabled():
            self.ui.btn_calib_tab.move(self.ui.btn_calib_tab.pos().x(),
                                       self.ui.btn_calib_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_calib_tab, "8pt")

        if not self.ui.btn_gen_tab.isEnabled():
            self.ui.btn_gen_tab.move(self.ui.btn_gen_tab.pos().x(),
                                     self.ui.btn_gen_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_gen_tab, "8pt")

        if not self.ui.btn_opt_tab.isEnabled():
            self.ui.btn_opt_tab.move(self.ui.btn_opt_tab.pos().x(),
                                     self.ui.btn_opt_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_opt_tab, "10pt")

        if not self.ui.btn_ref_tab.isEnabled():
            self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(),
                                     self.ui.btn_ref_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_ref_tab, "10pt")

    def set_style_sheet_btn_clicked(self, btn, font_size, right_border):
        btn.setStyleSheet("border: 2px solid gray;border-color:rgb(208,208,208);border-bottom-color: rgb(60, 60, 60); "
                          "border-radius: 8px;font: 700 " + font_size +
                          " \"Segoe UI\";padding: 0 8px;background: rgb(60, 60, 60);"
                          "color: rgb(208,208,208);" + right_border)

    def set_style_sheet_btn_unclicked(self, btn, font_size):
        btn.setStyleSheet("border: 2px solid gray;border-color:rgb(208,208,208);border-radius: 8px;font: 600 " +
                          font_size + "\"Segoe UI\";padding: 0 8px;"
                                      "background: rgb(60, 60, 60);color: rgb(208,208,208);")

    def clicked_btn_reference(self):
        self.move_btns_back()

        self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(), self.ui.btn_ref_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_ref_tab, "10pt", "border-right-color: rgb(60, 60, 60)")

        self.ui.btn_ref_tab.setEnabled(False)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.show()
        self.ui.widget_gen.hide()

    def clicked_btn_optical(self):
        self.move_btns_back()

        self.ui.btn_opt_tab.move(self.ui.btn_opt_tab.pos().x(), self.ui.btn_opt_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_opt_tab, "10pt", "border-right-color: rgb(60, 60, 60);")

        self.ui.btn_opt_tab.setEnabled(False)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)

        self.ui.widget_opt.show()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.hide()

    def clicked_btn_calib(self):
        self.move_btns_back()

        self.ui.btn_calib_tab.move(self.ui.btn_calib_tab.pos().x(),
                                   self.ui.btn_calib_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_calib_tab, "8pt", "border-right-color: rgb(60, 60, 60);")

        self.ui.btn_calib_tab.setEnabled(False)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.show()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.hide()

    def clicked_btn_gen(self):
        self.move_btns_back()

        self.ui.btn_gen_tab.move(self.ui.btn_gen_tab.pos().x(), self.ui.btn_gen_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_gen_tab, "8pt", "")

        self.ui.btn_gen_tab.setEnabled(False)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_opt_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.show()

    def save_as_settings(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save YAML File", window.subfolderConfig_path,
                                                   "YAML Files (*.yaml);;All Files (*)",
                                                   options=options)
        if file_path:
            window.current_conf = False
            window.save_config_file(False)
            with open(file_path, 'w') as file:
                yaml_dump(window.def_config, file)
            with open(file_path, 'r') as file:
                window.config = yaml_safe_load(file)
            window.current_conf = True
            window.config_file_path = file_path
            self.save_settings()

    def save_settings(self):
        window.window_scale_delta = self.slider_value / window.window_scale
        print(
            "VALUE : " + str(self.slider_value) + "/" + str(window.window_scale) + "=" + str(window.window_scale_delta))
        window.window_scale = self.slider_value

        window.ref_channel = self.ui.ref_channel_comboBox.currentText()
        window.ref_device_name = self.ui.ref_device_comboBox.currentText()
        window.calib_filter_data = self.ui.calib_filter_data_comboBox.currentText()

        window.ref_sample_rate = int(self.ui.ref_sampling_rate_line.text())
        window.opt_sampling_rate = int(self.ui.opt_sampling_rate_line.text())
        window.opt_project = self.ui.opt_loaded_project_line.text()
        window.opt_channels = int(self.ui.opt_channels_combobox.currentText())
        window.calib_gain_mark = int(self.ui.calib_gain_mark_line.text())
        window.calib_optical_sensitivity = float(self.ui.calib_opt_sensitivity_line.text())
        window.calib_optical_sens_tolerance = float(self.ui.calib_opt_sensitivity_toler_line.text())
        window.folder_main = self.ui.main_folder_line.text()
        window.folder_ref_export = self.ui.ref_exp_folder_line.text()
        window.folder_ref_export_raw = self.ui.ref_exp_folder_raw_line.text()
        window.folder_opt_export = self.ui.opt_exp_folder_line.text()
        window.folder_opt_export_raw = self.ui.opt_exp_folder_raw_line.text()
        window.folder_calibration_export = self.ui.calib_export_folder_line.text()
        window.folder_sentinel_D_folder = self.ui.opt_sentinel_fold_line.text()
        window.folder_sentinel_S_folder = self.ui.opt_sentinel_S_fold_line.text()
        window.calib_reference_sensitivity = float(self.ui.calib_ref_sensitivity_line.text())
        window.calib_l_flatness = int(self.ui.calib_flatness_left_line.text())
        window.calib_r_flatness = int(self.ui.calib_flatness_right_line.text())
        window.calib_angle_set_freq = int(self.ui.calib_agnelsetfreq_line.text())
        window.calib_phase_mark = int(self.ui.calib_phase_mark_line.text())

        window.calib_plot = self.ui.calib_plot_graphs_check.isChecked()
        window.calib_downsample = int(self.ui.calib_downsample_check.isChecked())
        window.calib_do_spectrum = int(self.ui.calib_do_spectrum_check.isChecked())

        window.generator_id = self.ui.gen_id_combobox.currentText()
        window.generator_sweep_time = int(self.ui.gen_sweep_time_line.text())
        window.generator_sweep_start_freq = int(self.ui.gen_start_freq_line.text())
        window.generator_sweep_stop_freq = int(self.ui.gen_stop_freq_line.text())
        window.generator_sweep_type = self.ui.gen_sweep_type_combobox.currentText()
        window.generator_max_mvpp = int(self.ui.gen_vpp_line.text())

        window.ref_measure_time = int(window.generator_sweep_time + 5)
        window.ref_number_of_samples = int(
            window.ref_measure_time * window.ref_sample_rate)

        window.save_config_file(True)

        self.close()

    def new_setting_enabled(self):
        self.load_settings()
        self.thread_check_new.nidaq_devices = self.nidaq_devices
        self.thread_check_new.all_configs = self.all_configs
        self.thread_check_new.resource = self.resources

    def load_settings(self):
        # load lineEdits
        _, value = self.slider_scale_get_real_value(window.window_scale)
        self.ui.slider_win_scale.setValue(value)
        self.ui.settings_scale2x_label.setText(str(window.window_scale) + "x")

        self.ui.main_folder_line.setText(window.folder_main)
        self.ui.ref_sampling_rate_line.setText(str(window.ref_sample_rate))
        self.ui.ref_exp_folder_line.setText(window.folder_ref_export)
        self.ui.ref_exp_folder_raw_line.setText(window.folder_ref_export_raw)
        self.ui.opt_sampling_rate_line.setText(str(window.opt_sampling_rate))
        self.ui.opt_exp_folder_line.setText(window.folder_opt_export)
        self.ui.opt_exp_folder_raw_line.setText(window.folder_opt_export_raw)
        self.ui.opt_sentinel_fold_line.setText(window.folder_sentinel_D_folder)
        self.ui.opt_loaded_project_line.setText(window.opt_project)
        self.ui.opt_channels_combobox.setCurrentText(str(window.opt_channels))
        self.ui.calib_gain_mark_line.setText(str(window.calib_gain_mark))
        self.ui.calib_opt_sensitivity_line.setText(str(window.calib_optical_sensitivity))
        self.ui.calib_opt_sensitivity_toler_line.setText(str(window.calib_optical_sens_tolerance))
        self.ui.calib_export_folder_line.setText(window.folder_calibration_export)
        self.ui.opt_sentinel_S_fold_line.setText(window.folder_sentinel_S_folder)
        self.ui.calib_ref_sensitivity_line.setText(str(window.calib_reference_sensitivity))
        self.ui.calib_flatness_left_line.setText(str(window.calib_l_flatness))
        self.ui.calib_flatness_right_line.setText(str(window.calib_r_flatness))
        self.ui.calib_phase_mark_line.setText(str(window.calib_phase_mark))
        self.ui.calib_agnelsetfreq_line.setText(str(window.calib_angle_set_freq))

        self.ui.gen_vpp_line.setText(str(window.generator_max_mvpp))
        self.ui.gen_sweep_type_combobox.setCurrentText(str(window.generator_sweep_type))
        self.ui.gen_stop_freq_line.setText(str(window.generator_sweep_stop_freq))
        self.ui.gen_start_freq_line.setText(str(window.generator_sweep_start_freq))
        self.ui.gen_sweep_time_line.setText(str(window.generator_sweep_time))
        # load checks
        self.ui.calib_downsample_check.setChecked(window.calib_downsample)
        self.ui.calib_do_spectrum_check.setChecked(window.calib_do_spectrum)
        self.ui.calib_plot_graphs_check.setChecked(window.calib_plot)
        # load comboBox
        # devices
        self.ui.ref_device_comboBox.blockSignals(True)
        self.ui.ref_device_comboBox.clear()
        system = nidaqmx_system.System.local()
        self.nidaq_devices = system.devices.device_names
        for device in self.nidaq_devices:
            self.ui.ref_device_comboBox.addItem(f'{device}')
        if window.ref_device_name is not None:
            self.ui.ref_device_comboBox.setCurrentText(window.ref_device_name)
        # channels
        self.ui.ref_channel_comboBox.blockSignals(True)
        self.ui.ref_channel_comboBox.clear()
        self.ui.ref_channel_comboBox.addItem('ai0')
        self.ui.ref_channel_comboBox.addItem('ai1')
        self.ui.ref_channel_comboBox.addItem('ai2')
        if window.ref_channel is not None:
            self.ui.ref_channel_comboBox.setCurrentText(window.ref_channel)
        # gen device ID
        self.ui.gen_id_combobox.clear()
        self.gen_id_combobox_clicked()
        self.ui.gen_id_combobox.setCurrentText(str(window.generator_id))
        # filter
        self.ui.calib_filter_data_comboBox.setCurrentText(window.calib_filter_data)
        self.all_configs = window.return_all_configs()
        # configs
        load_all_config_files(self.ui.select_config_file, self.all_configs, window.config_file_path)
        self.ui.ref_channel_comboBox.blockSignals(False)
        self.ui.ref_device_comboBox.blockSignals(False)

    def gen_id_combobox_clicked(self):
        self.ui.gen_id_combobox.blockSignals(True)
        self.ui.gen_id_combobox.clear()
        self.ui.gen_id_combobox.addItem("SELECT DEVICE")
        i = 1
        rm = pyvisa_ResourceManager()
        self.resources = rm.list_resources()
        for resource_name in self.resources:
            try:
                instrument = rm.open_resource(resource_name)
                instrument.close()
                self.ui.gen_id_combobox.addItem(str(resource_name))
                i += 1
            except Exception as e:
                print(self.resources)
                print(f"Error with {resource_name}: {e}")

        self.ui.gen_id_combobox.blockSignals(False)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        return folder_path

    def opt_sentinel_load_proj(self):
        if self.ui.opt_sentinel_fold_line.text() is not None:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Project",
                                                       directory=os_path.join(self.ui.opt_sentinel_fold_line.text(),
                                                                              "Sensors"))
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Project")

        print(file_path)
        if file_path:
            self.ui.opt_loaded_project_line.setText(os_path.basename(file_path))

    def select_config_file_combobox_changed(self, text):
        window.current_conf = False
        window.save_config_file(False)

        self.config_file = text
        self.config_file_path = os_path.join(window.subfolderConfig_path, self.config_file)
        window.config_file_path = self.config_file_path
        window.load_config_file()

        window.current_conf = True
        window.save_config_file(True)

        self.load_settings()

    def calib_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.calib_export_folder_line.setText(folder_path)

    def opt_sentinel_s_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.opt_sentinel_S_fold_line.setText(folder_path)

    def opt_sentinel_d_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.opt_sentinel_fold_line.setText(folder_path)

    def opt_export_raw_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.opt_exp_folder_raw_line.setText(folder_path)

    def opt_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.opt_exp_folder_line.setText(folder_path)

    def ref_export_raw_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.ref_exp_folder_raw_line.setText(folder_path)

    def ref_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.ref_exp_folder_line.setText(folder_path)

    def main_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.main_folder_line.setText(folder_path)

    def closeEvent(self, event):
        self.thread_check_new.terminate()
        if self.start:
            window.show()
        else:
            window.calib_window.show()
        super().closeEvent(event)

    def showEvent(self, event):
        center_on_screen(self)


#  okno merania + stavy...
class MyMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        from autoCalibration import Ui_AutoCalibration

        self.opt_sens_status_mapping = {
            0: ("OPT. SENSOR IS NOT CONNECTED", "orange"),
            1: ("OPT. SENSOR IS CONNECTED", "blue"),
            3: ("OPT. USB DEVICE DISCONNECTED!", "red", "black"),
            4: ("OPT. SENSOR IS NOT READY", "red"),
            5: ("OPT. SENSOR IS READY", "green"),
        }

        self.ref_sens_status_mapping = {
            0: ("REF. SENSOR IS NOT CONNECTED", "orange"),
            1: ("REF. SENSOR IS CONNECTED", "blue"),
            2: ("REF. SENSOR IS READY", "green"),
            3: ("REF. USB DEVICE DISCONNECTED!", "red", "black"),
            6: ("REF. SENSOR IS NOT READY", "red"),
        }

        self.sensor_gen_check = True
        self.thread_check_new_file = None
        self.config_file_path = None
        self.config_file = None
        self.settings_window = None
        self.measure = False
        self.S_N = None
        self.ref_init = 0
        self.remaining_time = 3
        self.sensor_ref_check = -1
        self.sensor_opt_check = -1

        self.ui = Ui_AutoCalibration()
        self.ui.setupUi(self)
        open_action = QAction("Options", self)
        open_action.triggered.connect(self.open_settings_window)
        self.ui.menuSettings.addAction(open_action)
        self.autoCalib = AutoCalibMain()

        self.ui.logo_label.setPixmap(QPixmap("../Working/images/logo.png"))

        self.ui.S_N_line.editingFinished.connect(self.set_s_n)
        self.ui.start_btn.clicked.connect(self.autoCalib.on_btn_start_clicked)
        self.ui.stop_btn.clicked.connect(self.emergency_stop_clicked)
        self.ui.plot_graph_check.stateChanged.connect(self.plot_check_changed)
        self.ui.select_config.currentTextChanged.connect(self.config_changed)
        self.ui.btn_load_wl.clicked.connect(self.btn_connect_load_wl)
        self.ui.progressBar.setValue(0)
        self.ui.start_btn.setEnabled(False)
        font = QFont("Arial", 10)
        font2 = QFont("Arial", 12)
        self.ui.output_browser_2.setFont(font)
        self.ui.output_browser.setFont(font)
        self.ui.output_browser_3.setFont(font2)
        self.ui.output_browser_3.setText("Work flow: \n1. CONNECT and TURN ON ALL device\n"
                                         "2. Properly mount optical sensor\n3. Properly mount reference sensor on top "
                                         "of the optical sensor\n"
                                         "4. Connect optical sensor to the interrogator\n5. Connect reference"
                                         " sensor to the NI USB device's 2nd channel\n"
                                         "6. Start calibration")

        self.ui.stop_btn.setHidden(True)
        self.ui.gen_status_label.setHidden(False)
        self.ui.gen_status_label_2.setHidden(True)
        self.change_sens_type_label()
        self.setWindowIcon(QIcon('../Working/images/logo_icon.png'))
        scale_app(self, window.window_scale)

    def plot_check_changed(self, state):
        if state == 2:
            window.calib_plot = True
        else:
            window.calib_plot = False
        window.save_config_file(True)

    def write_to_output_browser(self, text):
        self.ui.output_browser_3.setText(text)

    def change_sens_type_label(self):
        self.ui.label_opt_sens_type_label.setText(window.opt_sensor_type + "\'s")

    def emergency_stop_clicked(self):
        print("STOP")
        window.emergency_stop = True
        kill_sentinel(True, False)
        try:
            self.autoCalib.thread_ref_sens.task.close()
        except:
            pass
        self.autoCalib.thread_ref_sens.terminate()
        self.ui.stop_btn.setEnabled(False)
        self.ui.S_N_line.setEnabled(True)
        self.ui.select_config.setEnabled(True)
        self.ui.plot_graph_check.setEnabled(True)
        self.ui.menubar.setEnabled(True)
        self.ui.start_btn.setEnabled(True)
        self.measure = False

    def first_sentinel_start(self):
        start_sentinel_s(window.opt_project)
        self.thread_check_new_file = ThreadSentinelCheckNewFile()
        self.thread_check_new_file.finished.connect(self.start_modbus)
        self.thread_check_new_file.start()

    def start_modbus(self):
        kill_sentinel(True, False)
        QThread.msleep(100)
        start_sentinel_modbus(window.folder_sentinel_modbus_folder, window.folder_sentinel_D_folder, window.opt_project)

        os_chdir(window.folder_opt_export)

        if os_path.exists(window.calib_window.autoCalib.opt_sentinel_file_name + '.csv'):
            os_remove(window.calib_window.autoCalib.opt_sentinel_file_name + '.csv')
        QThread.msleep(100)
        window.calib_window.show()
        window.hide()
        QThread.msleep(100)

        self.autoCalib.start()

    def opt_emit(self, is_ready):
        self.sensor_opt_check = is_ready

    def gen_emit(self, is_ready):
        self.sensor_gen_check = is_ready

    def ref_emit(self, is_ready):
        self.sensor_ref_check = is_ready

    def check_sensors_ready(self):
        def update_status(label, mapping, check_value):
            text, color1, color2 = mapping.get(check_value, ("", "black", "black"))
            label.setText(text)
            label.setStyleSheet(f"color: {color1};")
            if check_value in {3} and label.isEnabled():
                label.setEnabled(False)
                label.setStyleSheet(f"color: {color2};")
            elif check_value in {3}:
                label.setEnabled(True)
                label.setStyleSheet(f"color: {color2};")
        if self.sensor_opt_check >= 0:
            update_status(self.ui.opt_sens_status_label, self.opt_sens_status_mapping, self.sensor_opt_check)
            update_status(self.ui.ref_sens_status_label, self.ref_sens_status_mapping, self.sensor_ref_check)

        if not self.sensor_gen_check:
            self.ui.gen_status_label_2.setHidden(False)
            self.ui.gen_status_label.setEnabled(not self.ui.gen_status_label.isEnabled())
            color = "red" if self.ui.gen_status_label.isEnabled() else "black"
            self.ui.gen_status_label.setStyleSheet(f"color: {color};")
            self.ui.gen_status_label_2.setStyleSheet(f"color: {color};")
        else:
            self.ui.gen_status_label.setStyleSheet("color: black;")
            self.ui.gen_status_label_2.setHidden(True)

        if window.opt_channels != 0 and self.ui.S_N_line.text().strip():
            self.ui.btn_load_wl.setEnabled(True)
            self.ui.start_btn.setEnabled(
                self.sensor_opt_check == 1 and self.sensor_ref_check == 1 and self.sensor_gen_check and not self.measure
            )
        else:
            self.ui.start_btn.setEnabled(False)
            self.ui.btn_load_wl.setEnabled(False)

        if self.sensor_ref_check == 2 and self.sensor_opt_check == 5:
            print("TERMINATION ------------------------")
            self.autoCalib.thread_check_sin_opt.termination = True
            self.autoCalib.thread_check_sin_ref.termination = True
            self.sensor_ref_check = 2
            self.sensor_opt_check = 5

    def config_changed(self, text):
        window.current_conf = False
        window.save_config_file(False)

        self.config_file = text
        self.config_file_path = os_path.join(window.subfolderConfig_path, self.config_file)
        window.config_file_path = self.config_file_path
        window.load_config_file()

        window.current_conf = True
        window.save_config_file(True)
        self.ui.plot_graph_check.setChecked(window.calib_plot)

    def set_s_n(self):
        self.S_N = self.ui.S_N_line.text()

    def btn_connect_load_wl(self):
        order_id = re_search(r'(-?\d+(\.\d+)?)', self.S_N).group(1)
        if window.opt_channels not in [0, 1]:
            kill_sentinel(False, True)
            set_wavelengths(order_id, window.folder_sentinel_D_folder, window.opt_project)
            start_sentinel_modbus(window.folder_sentinel_modbus_folder, window.folder_sentinel_D_folder,
                                  window.opt_project)

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(False)
        window.calib_window.hide()
        self.settings_window.show()

    def showEvent(self, event):
        scale_app(self, window.window_scale_delta)
        window.window_scale_delta = 1
        center_on_screen(self)
        self.ui.plot_graph_check.setChecked(window.calib_plot)
        load_all_config_files(self.ui.select_config, window.return_all_configs(), window.config_file_path)
        # label info o opt senz

        self.ui.label_start_freq.setText(str(window.generator_sweep_start_freq) + " Hz")
        self.ui.label_stop_freq.setText(str(window.generator_sweep_stop_freq) + " Hz")
        self.ui.label_mvpp.setText(str(window.generator_max_mvpp) + " mVpp")
        self.ui.label_sweep_type.setText(window.generator_sweep_type)
        self.ui.label_sweep_time.setText(str(window.generator_sweep_time) + " s")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to exit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clean up resources or save any data if needed before exiting
            kill_sentinel(True, True)
            pyplot_close('all')
            try:
                self.autoCalib.thread_check_sin_opt.termination = True
                self.autoCalib.thread_check_sin_ref.termination = True
            except:
                pass
            event.accept()
        else:
            event.ignore()


#  meranie + kalibrácia
class AutoCalibMain:

    def __init__(self):
        self.thread_control_gen = ThreadControlFuncGen(window.generator_id, window.generator_sweep_time,
                                                       window.generator_sweep_start_freq,
                                                       window.generator_sweep_stop_freq, window.generator_sweep_type,
                                                       window.generator_max_mvpp)
        self.thread_check_new_file = ThreadSentinelCheckNewFile()
        self.thread_ref_sens = ThreadRefSensDataCollection()
        self.thread_prog_bar = ThreadProgressBar(int(window.ref_measure_time))
        self.thread_check_sensors = ThreadSensorsCheckIfReady()
        self.thread_check_sin_opt = ThreadOptAndGenCheckIfReady("127.0.0.1", 501, 1, 100, 25, 0.003)
        self.thread_check_sin_ref = ThreadRefCheckIfReady(window.ref_device_name + '/' + window.ref_channel)
        self.acc_calib = None
        # self.refData = None
        self.current_date = None
        self.time_string = None
        self.opt_sentinel_file_name = None
        self.sensitivities_file = "sensitivities.csv"
        self.time_corrections_file = "time_corrections.csv"

    def ref_check_finished(self):
        print("END -------> REF CHECK")
        window.end_sens_test = True
        self.thread_check_new_file.start()

    def start(self):
        window.finished_measuring = False
        print("START() CHECKING SENSORS -------------")
        # print("SENS IS RUNNING ? : " + str(self.thread_check_sensors.isRunning()))
        # print("OPT IS RUNNING ? : " + str(self.thread_check_sin_opt.isRunning()))
        # print("REF IS RUNNING ? : " + str(self.thread_check_sin_ref.isRunning()))
        # print("CONTROL GEN IS RUNNING ? : " + str(self.thread_control_gen.isRunning()))
        # print("PROG IS RUNNING ? : " + str(self.thread_prog_bar.isRunning()))
        # print("REF MEASURE GEN IS RUNNING ? : " + str(self.thread_ref_sens.isRunning()))
        self.thread_control_gen.terminate()
        self.thread_prog_bar.terminate()
        self.thread_ref_sens.terminate()

        window.calib_window.measure = False

        self.thread_check_sin_ref = ThreadRefCheckIfReady(window.ref_device_name + '/' + window.ref_channel)
        self.thread_check_sin_ref.check_ready.connect(window.calib_window.ref_emit)
        self.thread_check_sin_ref.finished.connect(self.ref_check_finished)

        self.thread_check_sin_opt = ThreadOptAndGenCheckIfReady("127.0.0.1", 501, 1, 100, 25, 0.003)
        self.thread_check_sin_opt.check_ready_opt.connect(window.calib_window.opt_emit)
        self.thread_check_sin_opt.check_ready_gen.connect(window.calib_window.gen_emit)
        self.thread_check_sin_opt.finished.connect(self.opt_finished)
        if self.thread_check_sensors is None:
            print("BUILDING SENS CHECK....")
            self.thread_check_sensors = ThreadSensorsCheckIfReady()
            self.thread_check_sensors.check_ready.connect(window.calib_window.check_sensors_ready)
            # self.thread_check_sensors.finished.connect(self.thread_end_check_sens)
            self.thread_check_sensors.start()
        else:
            if not self.thread_check_sensors.isRunning():
                print("STARTING SENS CHECK....")
                self.thread_check_sensors = ThreadSensorsCheckIfReady()
                self.thread_check_sensors.check_ready.connect(window.calib_window.check_sensors_ready)
                # self.thread_check_sensors.finished.connect(self.thread_end_check_sens)
                self.thread_check_sensors.start()
            else:
                print("SENSORS CHECK IS RUNNING....")

        self.thread_check_sin_ref.start()
        self.thread_check_sin_opt.start()
        window.calib_window.ui.start_btn.setEnabled(False)
        window.calib_window.ui.start_btn.setHidden(False)
        window.calib_window.ui.stop_btn.setHidden(True)
        window.calib_window.ui.stop_btn.setEnabled(True)

    def opt_finished(self):
        print("END -------> OPT CHECK")

    # def thread_end_check_sens(self):
    #     window.calib_window.ui.start_btn.setEnabled(False)
    #     print("END ------> CHECK SENS")
    #     self.start()

    def thread_control_gen_finished(self):
        window.finished_measuring = False
        window.start_measuring = False
        window.start_sens_test = False
        window.end_sens_test = False
        rm = pyvisa_ResourceManager()
        instrument = rm.open_resource(window.generator_id)
        print("END -------> CONTROL GEN")
        instrument.write('OUTPut1:STATe OFF')
        if window.emergency_stop:
            window.calib_window.ui.start_btn.setEnabled(False)
            window.calib_window.ui.start_btn.setHidden(False)
            window.calib_window.ui.stop_btn.setHidden(True)
            window.calib_window.ui.stop_btn.setEnabled(True)
            window.emergency_stop = False

    def terminate_measure_threads(self):
        self.thread_ref_sens.terminate()
        kill_sentinel(True, False)

    def on_btn_start_clicked(self):  # start merania
        try:
            pyplot_close('all')
        except:
            pass

        start_calibration = True

        if os_path.exists(os_path.join(window.folder_calibration_export, window.calib_window.s_n + '.csv')):
            window.calib_window.setEnabled(False)
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Do you want to re-calibrate this sensor?")
            msgBox.setWindowTitle("Re-calibrate Sensor?")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Yes:
                start_calibration = True
            else:
                start_calibration = False
            window.calib_window.setEnabled(True)

        if start_calibration:
            window.calib_window.ui.output_browser.clear()
            window.calib_window.ui.output_browser_2.clear()
            window.start_measuring = False
            window.start_sens_test = False
            window.end_sens_test = False
            window.calib_window.ui.pass_status_label.setStyleSheet("color: rgba(170, 170, 127,150);")
            window.calib_window.ui.fail_status_label.setStyleSheet("color: rgba(170, 170, 127,150);")
            window.calib_window.ui.fail_status_label.setHidden(False)
            window.calib_window.ui.pass_status_label.setHidden(False)
            window.calib_window.measure = True
            window.calib_window.ui.S_N_line.setEnabled(False)
            window.calib_window.ui.select_config.setEnabled(False)
            window.calib_window.ui.plot_graph_check.setEnabled(False)
            window.calib_window.ui.menubar.setEnabled(False)
            window.calib_window.ui.start_btn.setEnabled(False)

            self.thread_control_gen = ThreadControlFuncGen(window.generator_id, window.generator_sweep_time,
                                                           window.generator_sweep_start_freq,
                                                           window.generator_sweep_stop_freq,
                                                           window.generator_sweep_type,
                                                           window.generator_max_mvpp)
            self.thread_control_gen.connected_status.connect(window.calib_window.gen_emit)
            self.thread_control_gen.step_status.connect(window.calib_window.write_to_output_browser)
            self.thread_control_gen.finished.connect(self.thread_control_gen_finished)

            self.thread_check_new_file = ThreadSentinelCheckNewFile()
            self.thread_check_new_file.finished.connect(self.thread_check_new_file_finished)

            self.thread_prog_bar = ThreadProgressBar(int(window.ref_measure_time))
            self.thread_ref_sens = ThreadRefSensDataCollection()
            #
            self.thread_prog_bar.finished.connect(self.thread_prog_bar_finished)
            self.thread_prog_bar.progress_signal.connect(update_progress_bar)
            self.thread_ref_sens.finished.connect(self.thread_ref_sens_finished)
            window.start_sens_test = True
            self.thread_control_gen.start()
            window.calib_window.ui.stop_btn.setHidden(False)
            window.calib_window.ui.start_btn.setHidden(True)
            window.calib_window.ui.start_btn.setEnabled(False)

    def save_data(self, data, elapsed_time):
        from datetime import date

        today = date.today()
        self.current_date = today.strftime("%b-%d-%Y")

        file_path = os_path.join(window.folder_ref_export, window.calib_window.s_n + '.csv')
        file_path_raw = os_path.join(window.folder_ref_export_raw, window.calib_window.s_n + '.csv')
        with open(file_path, 'w') as file:
            file.write("# " + self.current_date + '\n')
            file.write("# " + self.time_string + '\n')
            file.write(
                "# Dĺžka merania : " + str(window.ref_measure_time) + "s (" + str(round(elapsed_time / 1000, 2)) +
                "s)" + '\n')
            file.write("# Vzorkovacia frekvencia : " + str(window.ref_sample_rate) + '\n')
            file.write("# Počet vzoriek : " + str(window.ref_number_of_samples) + '\n')
            file.write("# Merane zrýchlenie :" + '\n')
            for item in data:
                file.write(str(item) + '\n')

        with open(file_path_raw, 'w') as file:
            for item in data:
                file.write(str(item) + '\n')

        print("Zapisane do txt")

    def check_new_files(self):
        # Get the initial set of files in the folder
        initial_files = set(os_listdir(window.folder_opt_export))

        while True:
            # Get the current set of files in the folder
            current_files = set(os_listdir(window.folder_opt_export))

            # Find the difference between the current and initial files
            new_files = current_files - initial_files

            if new_files:
                for file in new_files:
                    self.opt_sentinel_file_name = file
                break

    def thread_prog_bar_finished(self):
        print("END ------> PROG BAR")
        window.calib_window.ui.progressBar.setValue(0)
        window.calib_window.ui.start_btn.setEnabled(False)
        self.thread_ref_sens.wait()
        print("WAITING FINISHED")
        window.calib_window.ui.S_N_line.setEnabled(True)
        window.calib_window.ui.select_config.setEnabled(True)
        window.calib_window.ui.plot_graph_check.setEnabled(True)
        window.calib_window.ui.menubar.setEnabled(True)
        self.start()
        # self.thread_check_sensors.termination = True

    def thread_check_new_file_finished(self):
        self.thread_prog_bar.start()
        self.thread_ref_sens.start()
        window.start_measuring = True

    def thread_ref_sens_finished(self):
        print("CALIBRATION --------------->")
        if not window.emergency_stop:
            self.make_opt_raw(4)
            file_path = os_path.join(window.folder_main, self.sensitivities_file)
            if os_path.exists(file_path):
                os_remove(file_path)
            file_path = os_path.join(window.folder_main, self.time_corrections_file)
            if os_path.exists(file_path):
                os_remove(file_path)
            if window.opt_channels == 1:
                from AC_calibration_1FBG_v3 import ACCalib_1ch
                self.acc_calib = ACCalib_1ch(window.calib_window.s_n, window.starting_folder, window.folder_main,
                                             window.folder_opt_export_raw, window.folder_ref_export_raw,
                                             float(window.calib_reference_sensitivity), int(window.calib_gain_mark),
                                             int(window.opt_sampling_rate),
                                             int(window.ref_sample_rate), window.calib_filter_data,
                                             int(window.calib_downsample),
                                             int(window.calib_do_spectrum),
                                             int(window.calib_l_flatness),
                                             int(window.calib_r_flatness), int(window.calib_angle_set_freq),
                                             int(window.calib_phase_mark)).start(False,
                                                                                 window.calib_optical_sensitivity / 1000,
                                                                                 True, 0)
                self.acc_calib = ACCalib_1ch(window.calib_window.s_n, window.starting_folder, window.folder_main,
                                             window.folder_opt_export_raw, window.folder_ref_export_raw,
                                             float(window.calib_reference_sensitivity), int(window.calib_gain_mark),
                                             int(window.opt_sampling_rate),
                                             int(window.ref_sample_rate), window.calib_filter_data,
                                             int(window.calib_downsample),
                                             int(window.calib_do_spectrum),
                                             int(window.calib_l_flatness),
                                             int(window.calib_r_flatness), int(window.calib_angle_set_freq),
                                             int(window.calib_phase_mark)).start(window.calib_plot,
                                                                                 self.acc_calib[1] / 1000,
                                                                                 True, self.acc_calib[8])
                 # [0]>wavelength 1,[1]>sensitivity pm/g at gainMark,[2]>flatness_edge_l,
                # [3]>flatness_edge_r,[4]>sens. flatness,[5]>MAX acc,[6]>MIN acc,[7]>DIFF symmetry,[8]>TimeCorrection,
                # [9]>wavelength 2
            elif window.opt_channels == 2:
                from AC_calibration_2FBG_edit import ACCalib_2ch
                self.acc_calib = ACCalib_2ch(window.calib_window.s_n, window.starting_folder, window.folder_main,
                                             window.folder_opt_export_raw, window.folder_ref_export_raw,
                                             float(window.calib_reference_sensitivity), int(window.calib_gain_mark),
                                             int(window.opt_sampling_rate),
                                             int(window.ref_sample_rate), window.calib_filter_data,
                                             int(window.calib_downsample),
                                             int(window.calib_do_spectrum),
                                             int(window.calib_l_flatness),
                                             int(window.calib_r_flatness), int(window.calib_angle_set_freq),
                                             int(window.calib_phase_mark)).start(False,
                                                                                 window.calib_optical_sensitivity / 1000,
                                                                                 True, 0)
                self.acc_calib = ACCalib_2ch(window.calib_window.s_n, window.starting_folder, window.folder_main,
                                             window.folder_opt_export_raw, window.folder_ref_export_raw,
                                             float(window.calib_reference_sensitivity), int(window.calib_gain_mark),
                                             int(window.opt_sampling_rate),
                                             int(window.ref_sample_rate), window.calib_filter_data,
                                             int(window.calib_downsample),
                                             int(window.calib_do_spectrum),
                                             int(window.calib_l_flatness),
                                             int(window.calib_r_flatness), int(window.calib_angle_set_freq),
                                             int(window.calib_phase_mark)).start(window.calib_plot,
                                                                                 self.acc_calib[1] / 1000,
                                                                                 True, self.acc_calib[8])

                # [3]>flatness_edge_r,[4]>sens. flatness,[5]>MAX acc,[6]>MIN acc,[7]>DIFF symmetry,[8]>TimeCorrection,
                # [9]>wavelength 2

            self.save_calib_data()
            window.calib_window.ui.S_N_line.setEnabled(True)
            window.calib_window.ui.select_config.setEnabled(True)
            window.calib_window.ui.plot_graph_check.setEnabled(True)
            window.calib_window.ui.menubar.setEnabled(True)
            self.check_if_calib_is_valid()

    def check_if_calib_is_valid(self):
        print(str((window.calib_optical_sensitivity - window.calib_optical_sens_tolerance)) + "<=" + str(
            self.acc_calib[1]) + "<=" + str((window.calib_optical_sensitivity + window.calib_optical_sens_tolerance)))
        if (window.calib_optical_sensitivity - window.calib_optical_sens_tolerance) <= self.acc_calib[1] <= \
                (window.calib_optical_sensitivity + window.calib_optical_sens_tolerance):

            window.calib_window.ui.pass_status_label.setStyleSheet("color: green;")
            window.calib_window.ui.fail_status_label.setStyleSheet("color: rgba(170, 170, 127,150);")
        else:
            window.calib_window.ui.fail_status_label.setStyleSheet("color: red;")
            window.calib_window.ui.pass_status_label.setStyleSheet("color: rgba(170, 170, 127,150);")

    def save_calib_data(self):
        file_path = os_path.join(window.folder_calibration_export, window.calib_window.s_n + '.csv')
        window.calib_window.ui.output_browser_3.setText("Calibration results: " + '\n')

        if len(self.acc_calib) <= 9:
            window.calib_window.ui.output_browser.append("# Center wavelength :\n")
            window.calib_window.ui.output_browser_2.setText(str(self.acc_calib[0]) + ' nm\n')
        else:
            window.calib_window.ui.output_browser.append("Center wavelengths :\n")
            window.calib_window.ui.output_browser_2.setText(str(self.acc_calib[0]) + '; ' + str(self.acc_calib[9]) +
                                                            ' nm\n')

        window.calib_window.ui.output_browser.append("# Sensitivity : " + '\n\n' +
                                                     "# Sensitivity flatness : ")
        window.calib_window.ui.output_browser_2.append(str(round(self.acc_calib[1], 3)) + " pm/g at " +
                                                       str(window.calib_gain_mark) + " Hz\n\n" + str(
            self.acc_calib[4]) +
                                                       " between " + str(self.acc_calib[2]) + " Hz and " +
                                                       str(self.acc_calib[3]) + " Hz")

        with open(file_path, 'w') as file:
            file.write("# S/N :" + '\n' + '\t\t' + str(window.calib_window.s_n) + '\n')
            file.write("# Date :" + '\n' + '\t\t' + self.current_date + '\n')
            file.write("# Time : " + '\n' + '\t\t' + self.time_string + '\n')
            if len(self.acc_calib) <= 9:
                file.write("# Channels : " + '\n' + '\t\t' "1" + '\n')
                file.write("# Center wavelength : " + '\n' + '\t\t' + str(self.acc_calib[0]) + '\n')
            else:
                file.write("# Channels : " + '\n' + '\t\t' "2 \n")
                file.write("# Center wavelength : " + '\n' + '\t\t' + str(self.acc_calib[0]) + ';' +
                           str(self.acc_calib[9]) + '\n')
            file.write("# Sensitivity : " + '\n' + '\t\t' + str(self.acc_calib[1]) + " pm/g at " + str(
                window.calib_gain_mark) + " Hz" + '\n')
            file.write("# Sensitivity flatness : " + '\n' + '\t\t' + str(self.acc_calib[4]) + " between " + str(
                self.acc_calib[2]) + " Hz and " + str(self.acc_calib[3]) + " Hz" + '\n')
            file.write("# Difference in symmetry : " + '\n' + '\t\t' + str(self.acc_calib[7]) + " % " + '\n')

    def make_opt_raw(self, num_lines_to_skip):
        file_path = os_path.join(window.folder_opt_export, self.opt_sentinel_file_name)
        file_path_raw = os_path.join(window.folder_opt_export_raw, window.calib_window.s_n + '.csv')

        with open(file_path, 'r') as file:
            total_lines = sum(1 for line in file)

            # Reset the file pointer to the beginning
            file.seek(0)

            # Skip the specified number of lines
            for _ in range(num_lines_to_skip):
                next(file)

            # Initialize the extracted columns list
            extracted_columns = []

            # Determine the number of lines to read (excluding the last line)
            lines_to_read = total_lines - num_lines_to_skip - 1  # int(window.opt_sampling_rate*0.15)

            for _ in range(lines_to_read):
                line = file.readline()
                columns = line.strip().split(';')

                if window.opt_channels == 1 and len(columns) >= 3:
                    extracted_columns.append(columns[2].lstrip())
                elif window.opt_channels == 2 and len(columns) >= 4:
                    extracted_columns.append(columns[2].lstrip() + ' ' + columns[3].lstrip())

        with open(file_path_raw, 'w') as output_file:
            output_file.write('\n'.join(extracted_columns))

        os_chdir(window.folder_opt_export)

        if os_path.exists(window.calib_window.s_n + '.csv'):
            os_remove(window.calib_window.s_n + '.csv')

        os_rename(self.opt_sentinel_file_name, window.calib_window.s_n + '.csv')


if __name__ == "__main__":
    window = MyStartUpWindow()
    app.exec()
