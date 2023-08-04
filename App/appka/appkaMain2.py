import glob
import matplotlib
import pythoncom
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
import PyQt5.QtWidgets
import PyQt5.QtCore
from PyQt5.QtCore import QFileInfo
from AC_calibration_1FBG_v3 import ACCalib
import yaml
import nidaqmx
import time
import os
import wmi
from scipy.fft import fft
from nidaqmx.constants import AcquisitionType
from start_up import Ui_Setup
from autoCalibration import Ui_AutoCalibration
from settings import Ui_Settings
from pyModbusTCP.client import ModbusClient
import traceback
import sys
import subprocess
import csv
from itertools import zip_longest
import AC_functions_1FBG_v2 as fun


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("catched: ", tb)
    sys.exit(1)


# Install exception hook
sys.excepthook = excepthook


class ThreadWaitForMeasureFinish(PyQt5.QtCore.QThread):

    def run(self):
        window.calib_window.autoCalib.thread_opt_sens.wait()
        window.calib_window.autoCalib.thread_ref_sens.wait()


class ThreadOptReadSamplesModBus(PyQt5.QtCore.QThread):
    samples = None
    termination = False

    def __init__(self,  server_ip, server_port, unit_id):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.unit_id = unit_id

        self.file_name = window.calib_window.S_N
        self.measure_time = window.ref_measure_time
        self.channels = window.channels
        self.opt_freq = window.opt_sampling_rate
        self.folder = window.folder_opt_export_raw
        self.file_path = os.path.join(self.folder, self.file_name + ".csv")

    def run(self):
        client = ModbusClient(host=self.server_ip, port=self.server_port, unit_id=self.unit_id)
        client.open()
        samples = []
        if client.is_open:
            print("START OPT DATA COLLECTION")
            start_time = time.time()
            while not self.termination:
                regs = client.read_input_registers(100, 2)
                if regs is not None:
                    # Assume the first register is the whole number and the second is the decimal part
                    sample = regs[0] + regs[1] / 10000  # Add them to form a floating point number
                    samples.append(sample)
            end_time = time.time()
            print("STOP OPT DATA COLLECTION")
            print("time : " + str((end_time - start_time)) + " ,len samples: " +str(len(samples)))
            frequency = 1.0/((end_time - start_time)/float(len(samples)))
            print("\nRESAMPLING : " + str(frequency) + "/" + str(self.opt_freq))
            resampled_samples = fun.resample_by_interpolation(samples, frequency, self.opt_freq)
            with open(self.file_path, 'w') as file:
                print("SAVE OPT DATA")
                for item in resampled_samples:
                    file.write(str(item) + '\n')
                file.close()


class ThreadOptCheckIfReady(PyQt5.QtCore.QThread):
    check_ready = PyQt5.QtCore.pyqtSignal(int)

    def __init__(self, server_ip, server_port, unit_id, address, number_of_samples, threshold):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.unit_id = unit_id
        self.address = address
        self.number_of_samples = number_of_samples
        self.threshold = threshold
        self.termination = False

    def run(self):
        while not self.termination:
            self.check_ready.emit(self.check_if_ready())
            PyQt5.QtCore.QThread.msleep(333)

    def check_if_ready(self):
        client = ModbusClient(host=self.server_ip, port=self.server_port, unit_id=self.unit_id)
        client.open()
        i = 0
        samples = np.empty(self.number_of_samples)
        if client.is_open:
            # start_time = time.time()
            while i < self.number_of_samples:
                regs = client.read_input_registers(self.address, 2)
                if regs is not None:
                    # Assume the first register is the whole number and the second is the decimal part
                    sample = regs[0] + regs[1] / 10000  # Add them to form a floating point number
                    samples[i] = sample
                    i += 1
                    # print(sample)

            # end_time = time.time()
            # elapsed_time = end_time - start_time
            # # print(f"Elapsed time: {elapsed_time:.6f} seconds")
            # samples = fun.resample_by_interpolation(samples, 1 / (elapsed_time / self.number_of_samples), 1000)
            # samples = [(x - float((sum(samples) / float(self.number_of_samples)))) * 1000 for x in samples]
            #
            # amp = data_contains_sinus2(samples, 1000, 100)  # 1/(elapsed_time/self.number_of_samples)
            # print("Opt : " + str(amp) + " sampling rate : " + str(1 / (elapsed_time / self.number_of_samples)))
            return int(not (np.any(samples == 0.0)))
        else:
            client.open()
            # print("OPT. DEVICE IS DISCONNECTED \n")
            return 3


class ThreadProgressBar(PyQt5.QtCore.QThread):
    progress_signal = PyQt5.QtCore.pyqtSignal(int)
    finished_signal = PyQt5.QtCore.pyqtSignal()

    def __init__(self, argument):
        super().__init__()
        self.duration = argument

    def run(self):
        i = 1
        while i < self.duration:
            PyQt5.QtCore.QThread.msleep(1000)
            self.progress_signal.emit(i)
            i = i + 1
        self.finished_signal.emit()


class ThreadRefSensDataCollection(PyQt5.QtCore.QThread):
    finished_signal = PyQt5.QtCore.pyqtSignal()

    def run(self):
        window.calib_window.autoCalib.start_ref_sens_data_collection()
        self.finished_signal.emit()


def data_contains_sinus(samples, threshold):
    # Perform frequency domain analysis using Fourier Transform (FFT)
    fft_values = np.fft.fft(samples)
    amplitudes = np.abs(fft_values)
    max_amplitude = np.max(amplitudes)

    # Calculate the normalized amplitude of the dominant frequency
    normalized_amplitude = max_amplitude / len(samples)

    # Check if the waveform is sinusoidal based on the threshold
    if normalized_amplitude >= threshold:
        return True, normalized_amplitude
    else:
        return False, normalized_amplitude


def data_contains_sinus2(samples, sample_rate, peak_threshold):
    # Perform Fast Fourier Transform
    data = np.array(samples)
    yf = fft(data)
    xf = np.linspace(0.0, 1.0 / (2.0 / sample_rate), len(data) // 2)

    # Check if the signal forms a periodic waveform
    # If there is a peak in the frequency domain, we can say that there is a periodic signal
    peak_freqs = xf[np.abs(yf[:len(data) // 2]) > peak_threshold]

    return len(peak_freqs)


class ThreadSensorsCheckIfReady(PyQt5.QtCore.QThread):
    check_ready = PyQt5.QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.termination = False

    def run(self):
        while not self.termination:
            PyQt5.QtCore.QThread.msleep(250)
            self.check_ready.emit()


class ThreadRefCheckIfReady(PyQt5.QtCore.QThread):
    finished_signal = PyQt5.QtCore.pyqtSignal()
    check_ready = PyQt5.QtCore.pyqtSignal(int)

    def __init__(self, device_name_and_channel):
        super().__init__()
        self.termination = False
        self.task_sin = nidaqmx.Task()
        self.deviceName_channel = device_name_and_channel

    def run(self):
        sample_rate = 12800
        number_of_samples_per_channel = int(12800 / 13)

        #
        print("Start ref sens sinus check")
        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        while not self.termination:
            try:
                self.task_sin.ai_channels.add_ai_accel_chan(self.deviceName_channel, sensitivity=1000)

                # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
                self.task_sin.timing.cfg_samp_clk_timing(sample_rate,
                                                         sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
                self.task_sin.start()
                peaks = 0
                index = 0
                # 2 varianta
                while not self.termination:
                    data = self.task_sin.read(number_of_samples_per_channel=number_of_samples_per_channel,
                                              timeout=nidaqmx.constants.WAIT_INFINITELY)
                    # ready, amp = data_contains_sinus(data, 0.01)
                    peak = data_contains_sinus2(data, 12800, 1.75)
                    # print(peak)
                    peaks += peak
                    if index > 19:
                        calc = peaks / (index + 1)
                        print(calc)
                        if 4 <= calc <= 10:
                            self.check_ready.emit(1)
                        else:
                            self.check_ready.emit(0)
                        index = 0
                        peaks = 0
                    index += 1
                    # print("Ref : " + str(amp))
                    #
                    # self.check_ready.emit(int(ready))

                self.task_sin.stop()
                break
            except Exception as e:
                print(e)
                self.check_ready.emit(3)
            PyQt5.QtCore.QThread.msleep(333)
        self.task_sin.close()


def check_usb(opt_vendor_id, ref_vendor_id):
    c = wmi.WMI()
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

            # Check if this device's Vendor ID matches the one we're looking for
            if v_id.upper() == opt_vendor_id.upper():
                opt = True
            if v_id.upper() == ref_vendor_id.upper():
                ref = True
            if opt and ref:
                break
        except Exception as e:
            pass
            return False, False
    return opt, ref


class ThreadCheckDevicesConnected(PyQt5.QtCore.QThread):
    all_connected = PyQt5.QtCore.pyqtSignal(bool, bool)

    def __init__(self):
        super().__init__()
        self.opt_dev_vendor = 'BA8C'
        # self.ref_dev_vendor = '3923'
        self.ref_dev_vendor = '1093'
        self.termination = False

    def run(self):
        pythoncom.CoInitialize()
        while not self.termination:
            opt, ref = check_usb(self.opt_dev_vendor, self.ref_dev_vendor)
            # ref = True

            self.all_connected.emit(opt, ref)
            if opt and ref:
                PyQt5.QtCore.QThread.msleep(500)
            else:
                PyQt5.QtCore.QThread.msleep(250)


def clear_threads(threads):
    for thread in threads:
        thread.terminate()
    for thread in threads:
        thread.wait()


def plot_check_changed(state):
    if state == 2:
        window.calib_plot = True
    else:
        window.calib_plot = False
    window.save_config_file(True)


def channel_type_changed(index):
    window.channels = int(index)


class MyStartUpWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.ref_sample_rate = None
        self.ref_number_of_samples = None
        self.ref_measure_time = None
        self.current_conf = None
        self.ref_device_name = None
        self.ref_channel = None
        self.opt_sensor_type = None
        self.ref_connected = False
        self.modpoll_directory = "C:/Users/lukac/Desktop/Sylex/modpoll-3.10/win"
        self.starting_folder = os.getcwd()
        documents_path = os.path.expanduser('~/Documents')
        main_folder_name = 'Sylex_sensors_export'
        subfolder1a_name = 'reference'
        subfolder2a_name = 'optical'
        subfolder1b_name = 'reference_raw'
        subfolder2b_name = 'optical_raw'
        calibration_data_folder_name = 'calibration'

        self.main_folder_path = os.path.join(documents_path, main_folder_name)
        self.subfolderRef_path = os.path.join(self.main_folder_path, subfolder1a_name)
        self.subfolderOpt_path = os.path.join(self.main_folder_path, subfolder2a_name)
        self.subfolderRefRaw_path = os.path.join(self.main_folder_path, subfolder1b_name)
        self.subfolderOptRaw_path = os.path.join(self.main_folder_path, subfolder2b_name)
        self.subfolderCalibrationData = os.path.join(self.main_folder_path, calibration_data_folder_name)
        self.create_folders()
        self.channels = 0
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
            },
            'calibration': {
                'gain_mark': 150,
                'optical_sensitivity': 0,
                'filter_data': 'high-pass',
                'plot': 0,
                'downsample': 1,
                'do_spectrum': 1,
                'reference_sensitivity': 1,
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
            }
        }

        self.threads = []
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
        self.ui.opt_channel_comboBox.currentIndexChanged.connect(self.channel_type_changed)

        # buttons
        self.ui.start_app.setEnabled(False)

        # labels
        self.ui.status_opt_label.setText("Optical device DISCONNECTED")
        self.ui.status_opt_label.setStyleSheet("color: red;")
        self.ui.status_ref_label.setText("Reference device DISCONNECTED")
        self.ui.status_ref_label.setStyleSheet("color: red;")
        self.ui.null_detect_label.setStyleSheet("color: red;")
        self.ui.null_detect_label.setHidden(True)

        self.config_file_path = self.check_config_if_selected()
        self.setup_config()

        self.thread_check_usb_devices = ThreadCheckDevicesConnected()
        self.thread_check_usb_devices.all_connected.connect(self.all_dev_connected_signal)
        self.threads.append(self.thread_check_usb_devices)
        self.thread_check_usb_devices.start()
        self.calib_window = MyMainWindow()

    def showEvent(self, event):
        self.check_devices_load_comboboxes()

    def channel_type_changed(self, index):
        self.channels = int(index)

    def create_folders(self):
        if not os.path.exists(self.main_folder_path):
            # Create the main folder
            os.makedirs(self.main_folder_path)
            # print(f"Main folder created: {self.main_folder_path}")
        # else:
        # print(f"Main folder already exists: {self.main_folder_path}")

        # Create the subfolders inside the main folder
        os.makedirs(self.subfolderRef_path, exist_ok=True)
        os.makedirs(self.subfolderOpt_path, exist_ok=True)
        os.makedirs(self.subfolderRefRaw_path, exist_ok=True)
        os.makedirs(self.subfolderOptRaw_path, exist_ok=True)
        os.makedirs(self.subfolderCalibrationData, exist_ok=True)

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
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            self.config_contains_none = True

    def all_dev_connected_signal(self, opt_connected, ref_connected):
        if self.config_contains_none:
            if self.ui.null_detect_label.isEnabled():
                self.ui.null_detect_label.setHidden(False)
                self.ui.null_detect_label.setEnabled(False)
                self.ui.null_detect_label.setStyleSheet("color: black;")
            else:
                self.ui.null_detect_label.setHidden(False)
                self.ui.null_detect_label.setEnabled(True)
                self.ui.null_detect_label.setStyleSheet("color: red;")
            self.ui.start_app.setEnabled(False)
        else:
            self.ui.null_detect_label.setHidden(True)
            if ref_connected and opt_connected:
                self.ui.start_app.setEnabled(True)
            else:
                self.ui.start_app.setEnabled(False)

        if not ref_connected:
            if self.ui.status_ref_label.isEnabled():
                self.ui.status_ref_label.setEnabled(False)
                self.ui.status_ref_label.setText("Reference USB device DISCONNECTED")
                self.ui.status_ref_label.setStyleSheet("color: black;")
            else:
                self.ui.status_ref_label.setEnabled(True)
                self.ui.status_ref_label.setText("Reference USB device DISCONNECTED")
                self.ui.status_ref_label.setStyleSheet("color: red;")
            if self.ref_connected:
                self.check_devices_load_comboboxes()
                self.ref_connected = False
        else:
            self.ui.status_ref_label.setText("Reference USB device CONNECTED")
            self.ui.status_ref_label.setStyleSheet("color: green;")
            if not self.ref_connected:
                self.ref_connected = True
                self.check_devices_load_comboboxes()

        if not opt_connected:
            if self.ui.status_opt_label.isEnabled():
                self.ui.status_opt_label.setEnabled(False)
                self.ui.status_opt_label.setText("Optical USB device DISCONNECTED")
                self.ui.status_opt_label.setStyleSheet("color: black;")
            else:
                self.ui.status_opt_label.setEnabled(True)
                self.ui.status_opt_label.setText("Optical USB device DISCONNECTED")
                self.ui.status_opt_label.setStyleSheet("color: red;")
        else:
            self.ui.status_opt_label.setText("Optical USB device CONNECTED")
            self.ui.status_opt_label.setStyleSheet("color: green;")

    def sens_type_combobox_changed(self, text):
        self.opt_sensor_type = text
        self.save_config_file(True)

    def ref_channel_combobox_changed(self, text):
        self.ref_channel = text
        self.save_config_file(True)

    def ref_device_combobox_changed(self, text):
        if text != "NOT DETECTED":
            self.ref_device_name = text
        self.save_config_file(True)

    def return_all_configs(self):
        yaml_files = glob.glob(os.path.join(self.main_folder_path, '*.yaml'))
        return yaml_files

    def check_config_if_selected(self):
        yaml_files = self.return_all_configs()
        for yaml_file in yaml_files:
            config_file_path = os.path.join(self.main_folder_path, yaml_file)
            with open(config_file_path, 'r') as file:
                config = yaml.safe_load(file)
                if config['current']:
                    return config_file_path
        return None

    def setup_config(self):
        if self.config_file_path is not None and os.path.exists(self.config_file_path):
            self.load_config_file()
            self.check_devices_load_comboboxes()
        else:
            self.create_config_file()
            self.check_devices_load_comboboxes()

    def load_config_file(self):
        # print("load path in load config file : " + self.config_file_path)
        with open(self.config_file_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.current_conf = self.config['current']
        self.ref_channel = self.config['ref_device']['channel']
        self.ref_device_name = self.config['ref_device']['name']

        self.ref_measure_time = int(self.config['ref_measurement']['measure_time'])
        self.ref_number_of_samples = int(self.config['ref_measurement']['number_of_samples_per_channel'])
        self.ref_sample_rate = int(self.config['ref_measurement']['sample_rate'])

        self.opt_sensor_type = self.config['opt_measurement']['sensor_type']
        self.opt_sampling_rate = int(self.config['opt_measurement']['sampling_rate'])
        self.opt_project = self.config['opt_measurement']['project']

        self.calib_gain_mark = int(self.config['calibration']['gain_mark'])
        self.calib_optical_sensitivity = float(self.config['calibration']['optical_sensitivity'])
        self.calib_filter_data = self.config['calibration']['filter_data']
        self.calib_plot = self.config['calibration']['plot']
        self.calib_downsample = int(self.config['calibration']['downsample'])
        self.calib_do_spectrum = int(self.config['calibration']['do_spectrum'])
        self.calib_reference_sensitivity = float(self.config['calibration']['reference_sensitivity'])

        self.folder_main = self.config['save_data']['main_folder']
        self.folder_ref_export = self.config['save_data']['ref_export']
        self.folder_ref_export_raw = self.config['save_data']['ref_export_raw']
        self.folder_opt_export = self.config['save_data']['opt_export']
        self.folder_opt_export_raw = self.config['save_data']['opt_export_raw']
        self.folder_calibration_export = self.config['save_data']['calibration_export']
        self.folder_sentinel_D_folder = self.config['save_data']['sentinel_D_folder']
        self.folder_sentinel_S_folder = self.config['save_data']['sentinel_S_folder']
        self.S_N = self.config['save_data']['S_N']

        self.check_if_none()

    def create_config_file(self):
        yaml_name = 'default_config.yaml'
        self.config_file_path = os.path.join(self.main_folder_path, yaml_name)
        with open(self.config_file_path, 'w') as file:
            yaml.dump(self.def_config, file)

        self.load_config_file()

    def save_config_file(self, current_conf):
        self.config['current'] = current_conf
        self.config['ref_device']['channel'] = self.ref_channel
        self.config['ref_device']['name'] = self.ref_device_name

        self.config['ref_measurement']['measure_time'] = self.ref_measure_time
        self.config['ref_measurement']['number_of_samples_per_channel'] = self.ref_number_of_samples
        self.config['ref_measurement']['sample_rate'] = self.ref_sample_rate

        self.config['opt_measurement']['sensor_type'] = self.opt_sensor_type
        self.config['opt_measurement']['sampling_rate'] = self.opt_sampling_rate
        self.config['opt_measurement']['project'] = self.opt_project

        self.config['calibration']['gain_mark'] = self.calib_gain_mark
        self.config['calibration']['optical_sensitivity'] = self.calib_optical_sensitivity
        self.config['calibration']['filter_data'] = self.calib_filter_data
        self.config['calibration']['plot'] = self.calib_plot
        self.config['calibration']['downsample'] = self.calib_downsample
        self.config['calibration']['do_spectrum'] = self.calib_do_spectrum
        self.config['calibration']['reference_sensitivity'] = self.calib_reference_sensitivity

        self.config['save_data']['main_folder'] = self.folder_main
        self.config['save_data']['ref_export'] = self.folder_ref_export
        self.config['save_data']['ref_export_raw'] = self.folder_ref_export_raw
        self.config['save_data']['opt_export'] = self.folder_opt_export
        self.config['save_data']['opt_export_raw'] = self.folder_opt_export_raw
        self.config['save_data']['calibration_export'] = self.folder_calibration_export
        self.config['save_data']['sentinel_D_folder'] = self.folder_sentinel_D_folder
        self.config['save_data']['sentinel_S_folder'] = self.folder_sentinel_S_folder

        self.config['save_data']['S_N'] = self.S_N

        with open(self.config_file_path, 'w') as file:
            yaml.dump(self.config, file)

        self.check_if_none()

    def check_devices_load_comboboxes(self):
        self.ui.ref_device_comboBox.blockSignals(True)
        self.ui.ref_channel_comboBox.blockSignals(True)
        self.ui.sens_type_comboBox.blockSignals(True)

        self.ui.ref_device_comboBox.clear()
        self.ui.ref_channel_comboBox.clear()
        self.ui.sens_type_comboBox.clear()

        # load optical sensor types
        self.ui.sens_type_comboBox.addItem('accelerometer')
        if self.opt_sensor_type is not None:
            self.ui.sens_type_comboBox.setCurrentText(self.opt_sensor_type)

        # load ref sens devices
        system = nidaqmx.system.System.local()
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

        self.ui.ref_device_comboBox.blockSignals(False)
        self.ui.ref_channel_comboBox.blockSignals(False)
        self.ui.sens_type_comboBox.blockSignals(False)

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(True)
        self.hide()
        self.settings_window.show()

    def start_calib_app(self):
        # clear_threads(self.threads)
        # self.threads = []
        self.thread_check_usb_devices.termination = True
        self.thread_check_usb_devices.wait()
        self.hide()
        self.calib_window.show()
        self.calib_window.start()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to exit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clean up resources or save any data if needed before exiting
            # clear_threads(self.threads)
            # self.threads = []
            self.thread_check_usb_devices.termination = True
            self.thread_check_usb_devices.wait()
            event.accept()
        else:
            event.ignore()


# treba spravit default button a select folder buttony
class MySettingsWindow(QMainWindow):
    def __init__(self, start):
        super().__init__()
        self.config_file_path = None
        self.start = start
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.load_settings()
        self.config_file = None

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

        self.ui.calib_export_btn.clicked.connect(self.calib_export_folder_path_select)
        self.ui.save_as_btn.clicked.connect(self.save_as_settings)
        self.ui.select_config_file.currentTextChanged.connect(self.select_config_file_combobox_changed)
        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()

        self.btn_translate_dy = 8
        self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(), self.ui.btn_ref_tab.pos().y() + self.btn_translate_dy)
        self.ui.btn_ref_tab.setEnabled(False)

    def move_btns_back(self):
        if not self.ui.btn_calib_tab.isEnabled():
            self.ui.btn_calib_tab.move(self.ui.btn_calib_tab.pos().x(),
                                       self.ui.btn_calib_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_calib_tab, "8pt")

        if not self.ui.btn_opt_tab.isEnabled():
            self.ui.btn_opt_tab.move(self.ui.btn_opt_tab.pos().x(),
                                     self.ui.btn_opt_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_opt_tab, "10pt")

        if not self.ui.btn_ref_tab.isEnabled():
            self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(),
                                     self.ui.btn_ref_tab.pos().y() - self.btn_translate_dy)
            self.set_style_sheet_btn_unclicked(self.ui.btn_ref_tab, "10pt")

    def set_style_sheet_btn_clicked(self, btn, font_size, right_border):
        btn.setStyleSheet("border: 2px solid gray;border-color:rgb(208,208,208);border-bottom-color: rgb(44, 44, 44); "
                          "border-radius: 8px;font: 700 " + font_size + " \"Segoe UI\";padding: 0 8px;background: rgb(44, 44, 44);"
                                                                        "color: rgb(208,208,208);" + right_border)

    def set_style_sheet_btn_unclicked(self, btn, font_size):
        btn.setStyleSheet(
            "border: 2px solid gray;border-color:rgb(208,208,208);border-radius: 8px;font: 600 " + font_size + "\"Segoe UI\";padding: 0 8px;"
                                                                                                               "background: rgb(44, 44, 44);color: rgb(208,208,208);")

    def clicked_btn_reference(self):
        self.move_btns_back()

        self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(), self.ui.btn_ref_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_ref_tab, "10pt", "border-right-color: rgb(44,44,44)")

        self.ui.btn_ref_tab.setEnabled(False)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_calib_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.show()

    def clicked_btn_optical(self):
        self.move_btns_back()

        self.ui.btn_opt_tab.move(self.ui.btn_opt_tab.pos().x(), self.ui.btn_opt_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_opt_tab, "10pt", "border-right-color: rgb(44,44,44);")

        self.ui.btn_opt_tab.setEnabled(False)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_calib_tab.setEnabled(True)

        self.ui.widget_opt.show()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.hide()

    def clicked_btn_calib(self):
        self.move_btns_back()

        self.ui.btn_calib_tab.move(self.ui.btn_calib_tab.pos().x(),
                                   self.ui.btn_calib_tab.pos().y() + self.btn_translate_dy)
        self.set_style_sheet_btn_clicked(self.ui.btn_calib_tab, "8pt", "")

        self.ui.btn_calib_tab.setEnabled(False)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_opt_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.show()
        self.ui.widget_ref.hide()

    def save_as_settings(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save YAML File", window.main_folder_path,
                                                   "YAML Files (*.yaml);;All Files (*)",
                                                   options=options)
        if file_path:
            window.current_conf = False
            window.save_config_file(False)
            with open(file_path, 'w') as file:
                yaml.dump(window.def_config, file)
            with open(file_path, 'r') as file:
                window.config = yaml.safe_load(file)
            window.current_conf = True
            window.config_file_path = file_path
            self.save_settings()

    def save_settings(self):
        window.ref_channel = self.ui.ref_channel_comboBox.currentText()
        window.ref_device_name = self.ui.ref_device_comboBox.currentText()
        window.calib_filter_data = self.ui.calib_filter_data_comboBox.currentText()

        window.ref_measure_time = int(self.ui.mesure_time_line.text())
        window.ref_number_of_samples = int(
            float(self.ui.mesure_time_line.text()) * int(self.ui.ref_sampling_rate_line.text()))
        window.ref_sample_rate = int(self.ui.ref_sampling_rate_line.text())
        window.opt_sampling_rate = int(self.ui.opt_sampling_rate_line.text())
        window.opt_project = self.ui.opt_loaded_project_line.text()
        window.calib_gain_mark = int(self.ui.calib_gain_mark_line.text())
        window.calib_optical_sensitivity = float(self.ui.calib_opt_sensitivity_line.text())
        window.folder_main = self.ui.main_folder_line.text()
        window.folder_ref_export = self.ui.ref_exp_folder_line.text()
        window.folder_ref_export_raw = self.ui.ref_exp_folder_raw_line.text()
        window.folder_opt_export = self.ui.opt_exp_folder_line.text()
        window.folder_opt_export_raw = self.ui.opt_exp_folder_raw_line.text()
        window.folder_calibration_export = self.ui.calib_export_folder_line.text()
        window.folder_sentinel_D_folder = self.ui.opt_sentinel_fold_line.text()
        window.folder_sentinel_S_folder = self.ui.opt_sentinel_S_fold_line.text()
        window.calib_reference_sensitivity = float(self.ui.calib_ref_sensitivity_line.text())

        window.calib_plot = self.ui.calib_plot_graphs_check.isChecked()
        window.calib_downsample = int(self.ui.calib_downsample_check.isChecked())
        window.calib_do_spectrum = int(self.ui.calib_do_spectrum_check.isChecked())

        window.save_config_file(True)
        self.close()

    def load_settings(self):
        # load lineEdits
        self.ui.main_folder_line.setText(window.folder_main)
        self.ui.mesure_time_line.setText(str(window.ref_measure_time))
        self.ui.ref_sampling_rate_line.setText(str(window.ref_sample_rate))
        self.ui.ref_exp_folder_line.setText(window.folder_ref_export)
        self.ui.ref_exp_folder_raw_line.setText(window.folder_ref_export_raw)
        self.ui.opt_sampling_rate_line.setText(str(window.opt_sampling_rate))
        self.ui.opt_exp_folder_line.setText(window.folder_opt_export)
        self.ui.opt_exp_folder_raw_line.setText(window.folder_opt_export_raw)
        self.ui.opt_sentinel_fold_line.setText(window.folder_sentinel_D_folder)
        self.ui.opt_loaded_project_line.setText(window.opt_project)
        self.ui.calib_gain_mark_line.setText(str(window.calib_gain_mark))
        self.ui.calib_opt_sensitivity_line.setText(str(window.calib_optical_sensitivity))
        self.ui.calib_export_folder_line.setText(window.folder_calibration_export)
        self.ui.opt_sentinel_S_fold_line.setText(window.folder_sentinel_S_folder)
        self.ui.calib_ref_sensitivity_line.setText(str(window.calib_reference_sensitivity))
        # load checks
        self.ui.calib_downsample_check.setChecked(window.calib_downsample)
        self.ui.calib_do_spectrum_check.setChecked(window.calib_do_spectrum)
        self.ui.calib_plot_graphs_check.setChecked(window.calib_plot)
        # load comboBox
        # devices
        system = nidaqmx.system.System.local()
        for device in system.devices:
            self.ui.ref_device_comboBox.addItem(f'{device.name}')
        if window.ref_device_name is not None:
            self.ui.ref_device_comboBox.setCurrentText(window.ref_device_name)
        # channels
        self.ui.ref_channel_comboBox.addItem('ai0')
        self.ui.ref_channel_comboBox.addItem('ai1')
        self.ui.ref_channel_comboBox.addItem('ai2')
        if window.ref_channel is not None:
            self.ui.ref_channel_comboBox.setCurrentText(window.ref_channel)
        # filter
        self.ui.calib_filter_data_comboBox.setCurrentText(window.calib_filter_data)
        # configs
        self.load_all_config_files()

    def load_all_config_files(self):
        self.ui.select_config_file.blockSignals(True)
        self.ui.select_config_file.clear()
        yaml_files = window.return_all_configs()
        for yaml_file in yaml_files:
            self.ui.select_config_file.addItem(os.path.basename(yaml_file))

        self.ui.select_config_file.setCurrentText(QFileInfo(window.config_file_path).fileName())
        self.ui.select_config_file.blockSignals(False)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        return folder_path

    def opt_sentinel_load_proj(self):
        if self.ui.opt_sentinel_fold_line.text() is not None:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Project",
                                                       directory=os.path.join(self.ui.opt_sentinel_fold_line.text(),
                                                                              "Sensors"))
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Project")

        print(file_path)
        if file_path:
            self.ui.opt_loaded_project_line.setText(os.path.basename(file_path))

    def select_config_file_combobox_changed(self, text):
        window.current_conf = False
        window.save_config_file(False)

        self.config_file = text
        self.config_file_path = os.path.join(window.main_folder_path, self.config_file)
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

        if self.start:
            window.show()
        else:
            window.calib_window.show()
        super().closeEvent(event)


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config_file_path = None
        self.config_file = None
        self.settings_window = None
        self.S_N = None
        self.sensor_ref_check = 0
        self.sensor_opt_check = 0

        self.ui = Ui_AutoCalibration()
        self.ui.setupUi(self)
        open_action = PyQt5.QtWidgets.QAction("Options", self)
        open_action.triggered.connect(self.open_settings_window)
        self.ui.menuSettings.addAction(open_action)
        self.autoCalib = AutoCalibMain()

        self.ui.S_N_line.editingFinished.connect(self.set_s_n)
        self.ui.start_btn.clicked.connect(self.autoCalib.on_btn_start_clicked)
        self.ui.plot_graph_check.stateChanged.connect(plot_check_changed)
        self.ui.select_ses_type_channels_comboBox.currentIndexChanged.connect(channel_type_changed)
        self.ui.select_config.currentTextChanged.connect(self.config_changed)
        self.ui.progressBar.setValue(0)
        self.ui.start_btn.setEnabled(False)

    def start(self):
        self.autoCalib.start()

    def opt_emit(self, is_ready):
        self.sensor_opt_check = is_ready

    def ref_emit(self, is_ready):
        self.sensor_ref_check = is_ready

    def check_sensors_ready(self):
        if self.ui.select_ses_type_channels_comboBox.currentIndex() != 0 and self.ui.S_N_line.text().strip():
            if self.sensor_opt_check == 1 and self.sensor_ref_check == 1:
                self.ui.start_btn.setEnabled(True)
            else:
                self.ui.start_btn.setEnabled(False)
        else:
            self.ui.start_btn.setEnabled(False)

        if self.sensor_opt_check != 0:
            if self.sensor_opt_check == 1:
                self.ui.opt_sens_status_label.setText("OPT. SENSOR IS READY")
                self.ui.opt_sens_status_label.setStyleSheet("color: green;")
            else:
                self.ui.opt_sens_status_label.setText("OPT DEVICE DISCONNECTED!")
                if self.ui.opt_sens_status_label.isEnabled():
                    self.ui.opt_sens_status_label.setStyleSheet("color: red;")
                    self.ui.opt_sens_status_label.setEnabled(False)
                else:
                    self.ui.opt_sens_status_label.setStyleSheet("color: black;")
                    self.ui.opt_sens_status_label.setEnabled(True)
        else:
            self.ui.opt_sens_status_label.setText("OPT. SENSOR IS NOT READY")
            self.ui.opt_sens_status_label.setStyleSheet("color: orange;")

        if self.sensor_ref_check != 0:
            if self.sensor_ref_check == 1:
                self.ui.ref_sens_status_label.setText("REF. SENSOR IS READY")
                self.ui.ref_sens_status_label.setStyleSheet("color: green;")
            else:
                self.ui.ref_sens_status_label.setText("REF DEVICE DISCONNECTED!")
                if self.ui.ref_sens_status_label.isEnabled():
                    self.ui.ref_sens_status_label.setStyleSheet("color: red;")
                    self.ui.ref_sens_status_label.setEnabled(False)
                else:
                    self.ui.ref_sens_status_label.setStyleSheet("color: black;")
                    self.ui.ref_sens_status_label.setEnabled(True)
        else:
            self.ui.ref_sens_status_label.setText("REF. SENSOR IS NOT READY")
            self.ui.ref_sens_status_label.setStyleSheet("color: orange;")

    def config_changed(self, text):
        window.current_conf = False
        window.save_config_file(False)

        self.config_file = text
        self.config_file_path = os.path.join(window.main_folder_path, self.config_file)
        window.config_file_path = self.config_file_path
        window.load_config_file()

        window.current_conf = True
        window.save_config_file(True)
        self.ui.plot_graph_check.setChecked(window.calib_plot)

    def set_s_n(self):
        self.S_N = self.ui.S_N_line.text()

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(False)
        window.calib_window.hide()
        self.settings_window.show()

    def showEvent(self, event):
        self.ui.plot_graph_check.setChecked(window.calib_plot)
        self.load_all_config_files()
        self.ui.select_ses_type_channels_comboBox.setCurrentIndex(window.channels)

    def load_all_config_files(self):
        self.ui.select_config.blockSignals(True)
        self.ui.select_config.clear()
        yaml_files = window.return_all_configs()
        for yaml_file in yaml_files:
            self.ui.select_config.addItem(os.path.basename(yaml_file))

        self.ui.select_config.setCurrentText(QFileInfo(window.config_file_path).fileName())
        self.ui.select_config.blockSignals(False)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to exit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clean up resources or save any data if needed before exiting
            clear_threads(self.autoCalib.threads)
            self.autoCalib.threads = []
            matplotlib.pyplot.close('all')
            event.accept()
        else:
            event.ignore()


# def start_sentinel_s():  # ! vybrat path to .exe a project
#
#     sentinel_app = window.folder_sentinel_D_folder
#     sentinel_project = window.opt_project
#
#     os.chdir(sentinel_app)
#     os.system("start /min ClientApp_Dyn " + sentinel_project)


class AutoCalibMain:

    def __init__(self):
        self.thread_sens_wait = None
        self.thread_opt_sens = None
        self.thread_check_new_file = None
        self.thread_ref_sens = None
        self.thread_prog_bar = None
        self.thread_check_sensors = None
        self.thread_check_sin_opt = None
        self.thread_check_sin_ref = None
        self.acc_calib = None
        self.refData = None
        self.optData = None
        self.current_date = None
        self.time_string = None
        self.opt_sentinel_file_name = None
        self.sensitivities_file = "sensitivities.csv"
        self.time_corrections_file = "time_corrections.csv"
        self.threads = []

    def start(self):
        clear_threads(self.threads)
        self.threads = []
        self.thread_check_sin_ref = ThreadRefCheckIfReady(window.ref_device_name + '/' + window.ref_channel)
        self.thread_check_sin_ref.check_ready.connect(window.calib_window.ref_emit)

        self.thread_check_sin_opt = ThreadOptCheckIfReady("127.0.0.1", 501, 1, 100, 3700, 0.003)
        self.thread_check_sin_opt.check_ready.connect(window.calib_window.opt_emit)

        self.thread_check_sensors = ThreadSensorsCheckIfReady()
        self.thread_check_sensors.check_ready.connect(window.calib_window.check_sensors_ready)
        self.thread_check_sensors.finished.connect(self.thread_end_check_sens)

        self.threads.append(self.thread_check_sin_ref)
        self.threads.append(self.thread_check_sin_opt)
        self.threads.append(self.thread_check_sensors)

        self.thread_check_sin_ref.start()
        self.thread_check_sin_opt.start()
        self.thread_check_sensors.start()

    def thread_end_check_sens(self):
        window.calib_window.ui.start_btn.setEnabled(False)

    def on_btn_start_clicked(self):  # start merania
        self.thread_check_sin_ref.termination = True
        self.thread_check_sin_opt.termination = True
        self.thread_check_sensors.termination = True

        window.calib_window.ui.start_btn.setEnabled(False)
        window.calib_window.ui.S_N_line.setEnabled(False)
        window.calib_window.ui.select_config.setEnabled(False)
        window.calib_window.ui.select_ses_type_channels_comboBox.setEnabled(False)
        window.calib_window.ui.plot_graph_check.setEnabled(False)
        window.calib_window.ui.menubar.setEnabled(False)

        self.thread_prog_bar = ThreadProgressBar((int(window.ref_measure_time) + 4))
        self.thread_ref_sens = ThreadRefSensDataCollection()
        self.thread_opt_sens = ThreadOptReadSamplesModBus("127.0.0.1", 501, 1)
        self.thread_sens_wait = ThreadWaitForMeasureFinish()

        self.thread_prog_bar.finished_signal.connect(self.thread_prog_bar_finished)
        self.thread_prog_bar.progress_signal.connect(self.update_progress_bar)
        self.thread_sens_wait.finished.connect(self.thread_sens_finished)

        self.thread_check_sin_ref.wait()
        self.thread_check_sin_opt.wait()
        self.thread_check_sensors.wait()

        ## new code
        clear_threads(self.threads)
        self.threads = []
        self.threads.append(self.thread_prog_bar)
        self.threads.append(self.thread_ref_sens)
        self.threads.append(self.thread_opt_sens)
        self.thread_prog_bar.start()
        self.thread_ref_sens.start()
        self.thread_opt_sens.start()
        self.thread_sens_wait.start()

    def update_progress_bar(self, value):

        progress_sec = value
        if progress_sec < window.ref_measure_time:
            window.calib_window.ui.progressBar.setValue(int(100 * progress_sec / window.ref_measure_time))
        else:
            prog_finish = int(100 * progress_sec / window.ref_measure_time)
            if prog_finish < 100:
                window.calib_window.ui.progressBar.setValue(int(100 * progress_sec / window.ref_measure_time))
            else:
                window.calib_window.ui.progressBar.setValue(100)
                if progress_sec > (window.ref_measure_time + 2):
                    window.calib_window.ui.progressBar.setValue(0)

    def start_ref_sens_data_collection(self):

        from datetime import datetime

        with nidaqmx.Task() as task:
            # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
            task.ai_channels.add_ai_accel_chan(window.ref_device_name + '/' + window.ref_channel, sensitivity=1000)

            # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
            task.timing.cfg_samp_clk_timing(window.ref_sample_rate,
                                            sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                            samps_per_chan=int(window.ref_number_of_samples))

            print("START REF DATA COLLECTION")
            current_time = datetime.now().time()
            self.time_string = current_time.strftime("%H:%M:%S.%f")
            start_time = time.time()
            # spustenie získavania vzoriek
            task.start()

            # čítam získane vzorky
            data = task.read(number_of_samples_per_channel=window.ref_number_of_samples,
                             timeout=nidaqmx.constants.WAIT_INFINITELY)

            end_time = time.time()

            # stop
            task.stop()
            print("STOP REF DATA COLLECTION")

            # dĺžka merania
            elapsed_time = (end_time - start_time) * 1000
            # print(f"Cas trvania merania: {elapsed_time:.2f} ms")

            # ulozenie dát do txt súboru
            self.save_data(data, elapsed_time)
            self.refData = data
            # task.close()
            self.thread_opt_sens.termination = True

    def save_data(self, data, elapsed_time):
        from datetime import date

        today = date.today()
        self.current_date = today.strftime("%b-%d-%Y")

        file_path = os.path.join(window.folder_ref_export, window.calib_window.S_N + '.csv')
        file_path_raw = os.path.join(window.folder_ref_export_raw, window.calib_window.S_N + '.csv')
        print("SAVE REF DATA")
        with open(file_path, 'w') as file:
            file.write("# " + self.current_date + '\n')
            file.write("# " + self.time_string + '\n')
            file.write("# Dĺžka merania : " + str(window.ref_measure_time) + "s (" + str(
                round(elapsed_time / 1000, 2)) + "s)" + '\n')
            file.write("# Vzorkovacia frekvencia : " + str(window.ref_sample_rate) + '\n')
            file.write("# Počet vzoriek : " + str(window.ref_number_of_samples) + '\n')
            file.write("# Merane zrýchlenie :" + '\n')
            for item in data:
                file.write(str(item) + '\n')

        with open(file_path_raw, 'w') as file:
            for item in data:
                file.write(str(item) + '\n')

        print("Zapisane do txt")

    def thread_prog_bar_finished(self):
        self.start()

    def thread_sens_finished(self):
        # self.make_opt_raw(4)
        index = window.channels
        file_path = os.path.join(window.folder_main, self.sensitivities_file)
        if os.path.exists(file_path):
            os.remove(file_path)
        file_path = os.path.join(window.folder_main, self.time_corrections_file)
        if os.path.exists(file_path):
            os.remove(file_path)
        if index == 1:
            print("START CALIB")
            acc_script = ACCalib(window.calib_window.S_N, window.starting_folder, window.folder_main,
                                 window.folder_opt_export_raw,
                                 window.folder_ref_export_raw, window.calib_reference_sensitivity,
                                 window.calib_gain_mark, window.opt_sampling_rate, window.ref_sample_rate,
                                 window.calib_filter_data, window.calib_downsample, window.calib_do_spectrum,
                                 window.calib_optical_sensitivity)

            acc_script.start(0)
            self.acc_calib = acc_script.start(1)  # [0]>wavelength,[1]>sensitivity pm/g at gainMark,[2]>flatness_edge_l,
            # [3]>flatness_edge_r,[4]>sens. flatness,[5]>MAX acc,[6]>MIN acc,[7]>DIFF symmetry,[8]>TimeCorrection
        # elif index == 2:

        # pridaj spracovanie pre 2-channel acc

        self.save_calib_data()
        window.calib_window.ui.S_N_line.setEnabled(True)
        window.calib_window.ui.select_config.setEnabled(True)
        window.calib_window.ui.select_ses_type_channels_comboBox.setEnabled(True)
        window.calib_window.ui.plot_graph_check.setEnabled(True)
        window.calib_window.ui.menubar.setEnabled(True)

    def save_calib_data(self):
        file_path = os.path.join(window.folder_calibration_export, window.calib_window.S_N + '.csv')
        window.calib_window.ui.output_browser.setText("Calibration results: " + '\n' + '\n' +
                                                      "# S/N :" + '\t \t' + window.calib_window.S_N + '\n' +
                                                      "# Date :" + '\t \t' + self.current_date + '\n' +
                                                      "# Time : " + '\t \t' + self.time_string + '\n' +
                                                      "# Center wavelength : " + '\t \t' + str(
            self.acc_calib[0]) + '\n' +
                                                      "# Sensitivity : " + '\t \t' + str(
            self.acc_calib[1]) + " pm/g at " +
                                                      str(window.calib_gain_mark) + " Hz" + '\n' +
                                                      "# Sensitivity flatness : " + '\t \t' + str(
            self.acc_calib[4]) + " between " +
                                                      str(self.acc_calib[2]) + " Hz and " + str(
            self.acc_calib[3]) + " Hz")

        with open(file_path, 'w') as file:
            file.write("# S/N :" + '\n' + '\t' + "place holder" + '\n')
            file.write("# Date :" + '\n' + '\t' + self.current_date + '\n')
            file.write("# Time : " + '\n' + '\t' + self.time_string + '\n')
            file.write("# Center wavelength : " + '\n' + '\t' + str(self.acc_calib[0]) + '\n')
            file.write("# Sensitivity : " + '\n' + '\t' + str(self.acc_calib[1]) + " pm/g at " + str(
                window.calib_gain_mark) + " Hz" + '\n')
            file.write("# Sensitivity flatness : " + '\n' + '\t' + str(self.acc_calib[4]) + " between " + str(
                self.acc_calib[2]) + " Hz and " + str(self.acc_calib[3]) + " Hz" + '\n')

    def make_opt_raw(self, num_lines_to_skip):
        file_path = os.path.join(window.folder_opt_export, self.opt_sentinel_file_name)
        file_path_raw = os.path.join(window.folder_opt_export_raw, window.calib_window.S_N + '.csv')

        with open(file_path, 'r') as file:
            # Skip the specified number of lines
            for _ in range(num_lines_to_skip):
                next(file)

            # Read the third column from each line
            third_columns = []
            for line in file:
                columns = line.strip().split(';')
                if len(columns) >= 3:
                    third_columns.append(columns[2].lstrip())

        with open(file_path_raw, 'w') as output_file:
            output_file.write('\n'.join(third_columns))

        os.chdir(window.folder_opt_export)

        if os.path.exists(window.calib_window.S_N + '.csv'):
            os.remove(window.calib_window.S_N + '.csv')

        os.rename(self.opt_sentinel_file_name, window.calib_window.S_N + '.csv')


if __name__ == "__main__":
    app = QApplication([])
    window = MyStartUpWindow()
    window.show()
    app.exec()
