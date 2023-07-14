import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
import PyQt5.QtWidgets
import PyQt5.QtCore
from AC_calibration_1FBG_v3 import ACCalib
import yaml
import nidaqmx
import time
import os
from scipy.fft import fft
from nidaqmx.constants import AcquisitionType
from start_up import Ui_Setup
from autoCalibration import Ui_AutoCalibration
from settings import Ui_Settings

# class start_timer_thread(PyQt5.QtCore.QThread):
#     progress_signal = PyQt5.QtCore.pyqtSignal(int)
#     finished_signal = PyQt5.QtCore.pyqtSignal()
#     def __init__(self, argument):
#         super().__init__()
#         self.duration = argument
#
#     def run(self):
#         kali.ui.label_progress.setText("Starting data collection")
#         i = 1
#         while i < self.duration:
#             PyQt5.QtCore.QThread.msleep(1000)
#             self.progress_signal.emit(i)
#             i = i + 1
#         self.finished_signal.emit()
#
# class start_ref_sens_data_collection_thread(PyQt5.QtCore.QThread):
#     finished_signal = PyQt5.QtCore.pyqtSignal()
#
#     def run(self):
#         kali.start_ref_sens_data_collection()
#         self.finished_signal.emit()
#
# class start_check_new_file_thread(PyQt5.QtCore.QThread):
#     finished_signal = PyQt5.QtCore.pyqtSignal()
#
#     def run(self):
#         print("Start check thread")
#         kali.check_new_files()
#         self.finished_signal.emit()
#
# class start_ref_check_sin_thread(PyQt5.QtCore.QThread):
#     finished_signal = PyQt5.QtCore.pyqtSignal()
#
#     def __init__(self, deviceName_channel):
#         super().__init__()
#         self.termination = False
#         self.task_sin = nidaqmx.Task()
#         self.deviceName_channel = deviceName_channel
#
#     def run(self):
#         sample_rate = 12800
#         number_of_samples_per_channel = int(12800 / 3)
#         sin_threshold = 0.004
#         #
#         print("Start ref sens sinus check")
#         # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
#         self.task_sin.ai_channels.add_ai_accel_chan(self.deviceName_channel, sensitivity=1000)
#
#         # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
#         self.task_sin.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
#         self.task_sin.start()
#
#         ## 2 varianta
#         while not self.termination:
#             data = self.task_sin.read(number_of_samples_per_channel=number_of_samples_per_channel,
#                                       timeout=nidaqmx.constants.WAIT_INFINITELY)
#             if self.is_sinus2(data, sample_rate):  # self.is_sinus(data, sin_threshold):
#                 kali.ui.btn_start.setEnabled(True)
#                 print("REF IS READY \n")
#             else:
#                 kali.ui.btn_start.setEnabled(False)
#                 print("INSTALL REF SENS \n")
#         kali.ui.btn_start.setEnabled(False)
#         self.task_sin.stop()
#
#     def is_sinus(self, samples, threshold):
#         # Perform frequency domain analysis using Fourier Transform (FFT)
#         fft_values = np.fft.fft(samples)
#         amplitudes = np.abs(fft_values)
#         max_amplitude = np.max(amplitudes)
#
#         # Calculate the normalized amplitude of the dominant frequency
#         normalized_amplitude = max_amplitude / len(samples)
#
#         # Check if the waveform is sinusoidal based on the threshold
#         print(normalized_amplitude)
#         if normalized_amplitude >= threshold:
#             return True
#         else:
#             return False
#
#     def is_sinus2(self, samples, sample_rate):
#         # Perform Fast Fourier Transform
#         data = np.array(samples)
#         yf = fft(data)
#         xf = np.linspace(0.0, 1.0 / (2.0 / sample_rate), len(data) // 2)
#
#         # Check if the signal forms a periodic waveform
#         # If there is a peak in the frequency domain, we can say that there is a periodic signal
#         peak_threshold = 10  # adjust this threshold according to your needs
#         peak_freqs = xf[np.abs(yf[:len(data) // 2]) > peak_threshold]
#         if len(peak_freqs) > 0:
#             return True
#         else:
#             return False

class MyStartUpWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = None

        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        # connect btn
        self.ui.open_settings_btn.clicked.connect(self.open_settings_window)
        self.ui.start_app.clicked.connect(self.start_calib_app)
        self.ui.refresh_btn.clicked.connect(self.setup_config)
        # connect comboBox
        self.ui.sens_type_comboBox.currentTextChanged.connect(self.sens_type_comboBox_changed)
        self.ui.ref_channel_comboBox.currentTextChanged.connect(self.ref_channel_comboBox_changed)
        self.ui.ref_device_comboBox.currentTextChanged.connect(self.ref_device_comboBox_changed)

        # buttons
        self.ui.start_app.setEnabled(False)

        # labels
        self.ui.status_opt_label.setText("Optical device DOWN")
        self.ui.status_opt_label.setStyleSheet("color: red;")
        self.ui.status_ref_label.setText("Reference device DOWN")
        self.ui.status_ref_label.setStyleSheet("color: red;")
        self.ui.null_detect_label.setStyleSheet("color: red;")
        self.ui.null_detect_label.setHidden(True)

        self.config_file_path = os.path.join(os.getcwd(), 'a_ref_config.yaml')
        self.setup_config()

    def sens_type_comboBox_changed(self, text):
        self.opt_sensor_type = text
        self.save_config_file()

    def ref_channel_comboBox_changed(self, text):
        self.ref_channel = text
        self.save_config_file()

    def ref_device_comboBox_changed(self, text):
        self.ref_device_name = text
        self.save_config_file()

    def setup_config(self):
        if os.path.exists(self.config_file_path):
            self.check_devices_load_comboBoxes(self.load_config_file())
        else:
            self.check_devices_load_comboBoxes(self.create_config_file())

    def load_config_file(self):
        with open(self.config_file_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.ref_channel = self.config['ref_device']['channel']
        self.ref_device_name = self.config['ref_device']['name']

        self.ref_measure_time = self.config['ref_measurement']['measure_time']
        self.ref_number_of_samples = self.config['ref_measurement']['number_of_samples_per_channel']
        self.ref_sample_rate = self.config['ref_measurement']['sample_rate']

        self.opt_sensor_type = self.config['opt_measurement']['sensor_type']
        self.opt_sampling_rate = self.config['opt_measurement']['sampling_rate']
        self.opt_project = self.config['opt_measurement']['project']

        self.calib_gain_mark = self.config['calibration']['gain_mark']
        self.calib_optical_sensitivity = self.config['calibration']['optical_sensitivity']
        self.calib_filter_data = self.config['calibration']['filter_data']
        self.calib_plot = self.config['calibration']['plot']
        self.calib_downsample = self.config['calibration']['downsample']
        self.calib_do_spectrum = self.config['calibration']['do_spectrum']

        self.folder_main = self.config['save_data']['main_folder']
        self.folder_ref_export = self.config['save_data']['ref_export']
        self.folder_ref_export_raw = self.config['save_data']['ref_export_raw']
        self.folder_opt_export = self.config['save_data']['opt_export']
        self.folder_opt_export_raw = self.config['save_data']['opt_export_raw']
        self.folder_calibration_export = self.config['save_data']['calibration_export']
        self.folder_sentinel_folder = self.config['save_data']['sentinel_folder']
        self.S_N = self.config['save_data']['S_N']

        return any(value is None for value in self.config.values())

    def create_config_file(self):
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

        config = {
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
            },
            'save_data': {
                'main_folder': self.main_folder_path,
                'ref_export': self.subfolderRef_path,
                'ref_export_raw': self.subfolderRefRaw_path,
                'opt_export': self.subfolderOpt_path,
                'opt_export_raw': self.subfolderOptRaw_path,
                'calibration_export': self.subfolderCalibrationData,
                'sentinel_folder': None,
                'S_N': 'measured_data.csv'
            }
        }

        with open(self.config_file_path, 'w') as file:
            yaml.dump(config, file)

        return True

    def save_config_file(self):
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

        self.config['save_data']['main_folder'] = self.folder_main
        self.config['save_data']['ref_export'] = self.folder_ref_export
        self.config['save_data']['ref_export_raw'] = self.folder_ref_export_raw
        self.config['save_data']['opt_export'] = self.folder_opt_export
        self.config['save_data']['opt_export_raw'] = self.folder_opt_export_raw
        self.config['save_data']['calibration_export'] = self.folder_calibration_export
        self.config['save_data']['sentinel_folder'] = self.folder_sentinel_folder
        self.config['save_data']['S_N'] = self.S_N

        with open(self.config_file_path, 'w') as file:
            yaml.dump(self.config, file)

    def check_devices_load_comboBoxes(self, none):
        self.ui.ref_device_comboBox.clear()
        self.ui.ref_channel_comboBox.clear()
        self.ui.sens_type_comboBox.clear()

        start_btn_enable = False

        # load optical sensor types
        self.ui.sens_type_comboBox.addItem('accelerometer')
        self.ui.sens_type_comboBox.addItem('test')
        if self.opt_sensor_type is not None:
            self.ui.sens_type_comboBox.setCurrentText(self.opt_sensor_type)

        # load ref sens devices
        system = nidaqmx.system.System.local()

        for device in system.devices:
            self.ui.status_ref_label.setText("Reference device UP")
            self.ui.status_ref_label.setStyleSheet("color: green;")
            start_btn_enable = True
            self.ui.ref_device_comboBox.addItem(f'{device}')
        if self.ref_device_name is not None:
            self.ui.ref_device_comboBox.setCurrentText(self.ref_device_name)

        # load ref sens channels
        self.ui.ref_channel_comboBox.addItem('ai0')
        self.ui.ref_channel_comboBox.addItem('ai1')
        self.ui.ref_channel_comboBox.addItem('ai2')
        if self.ref_channel is not None:
            self.ui.ref_channel_comboBox.setCurrentText(self.ref_channel)

        self.ui.status_opt_label.setText("Optical device unknown")
        self.ui.status_opt_label.setStyleSheet("color: orange;")

        if none:
            self.ui.null_detect_label.setHiddne(False)
            start_btn_enable = False

        if start_btn_enable:
            self.ui.start_app.setEnabled(True)

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(True)
        window.hide()
        self.settings_window.show()

    def start_calib_app(self):
        self.calib_window = MyMainWindow()
        window.hide()
        self.calib_window.show()

# treba spravit default button a select folder buttony
class MySettingsWindow(QMainWindow):
    def __init__(self, start):
        super().__init__()
        self.start = start
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.load_settings()

        self.ui.save_btn.clicked.connect(self.save_settings)
        self.ui.cancel_btn.clicked.connect(self.load_settings)

    def save_settings(self):
        window.ref_channel = self.ui.ref_channel_comboBox.currentText()
        window.ref_device_name = self.ui.ref_device_comboBox.currentText()
        window.calib_filter_data = self.ui.calib_filter_data_comboBox.currentText()

        window.ref_measure_time = self.ui.mesure_time_line.text()
        window.ref_number_of_samples = int(float(self.ui.mesure_time_line.text())*int(self.ui.ref_sampling_rate_line.text()))
        window.ref_sample_rate = self.ui.ref_sampling_rate_line.text()
        window.opt_sampling_rate = self.ui.opt_sampling_rate_line.text()
        window.opt_project = self.ui.opt_loaded_project_line.text()
        window.calib_gain_mark = self.ui.calib_gain_mark_line.text()
        window.calib_optical_sensitivity = self.ui.calib_opt_sensitivity_line.text()
        window.folder_main = self.ui.main_folder_line.text()
        window.folder_ref_export = self.ui.ref_exp_folder_line.text()
        window.folder_ref_export_raw = self.ui.ref_exp_folder_raw_line.text()
        window.folder_opt_export = self.ui.opt_exp_folder_line.text()
        window.folder_opt_export_raw = self.ui.opt_exp_folder_raw_line.text()
        window.folder_calibration_export = self.ui.calib_export_folder_line.text()
        window.folder_sentinel_folder = self.ui.opt_sentinel_fold_line.text()

        window.calib_plot = int(self.ui.calib_plot_graphs_check.isChecked())
        window.calib_downsample = int(self.ui.calib_downsample_check.isChecked())
        window.calib_do_spectrum = int(self.ui.calib_do_spectrum_check.isChecked())

        window.save_config_file()
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
        self.ui.opt_sentinel_fold_line.setText(window.folder_sentinel_folder)
        self.ui.opt_loaded_project_line.setText(window.opt_project)
        self.ui.calib_gain_mark_line.setText(str(window.calib_gain_mark))
        self.ui.calib_opt_sensitivity_line.setText(str(window.calib_optical_sensitivity))
        self.ui.calib_export_folder_line.setText(window.folder_calibration_export)
        # load checks
        self.ui.calib_downsample_check.setChecked(window.calib_downsample)
        self.ui.calib_do_spectrum_check.setChecked(window.calib_do_spectrum)
        self.ui.calib_plot_graphs_check.setChecked(window.calib_plot)
        # load comboBox
        # devices
        system = nidaqmx.system.System.local()
        for device in system.devices:
            self.ui.ref_device_comboBox.addItem(f'{device}')
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

    def closeEvent(self, event):

        if self.start:
            window.show()
        else:
            window.calib_window.show()
        super().closeEvent(event)

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_AutoCalibration()
        self.ui.setupUi(self)
        open_action = PyQt5.QtWidgets.QAction("Options", self)
        open_action.triggered.connect(self.open_settings_window)
        self.ui.menuSettings.addAction(open_action)

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(False)
        window.calib_window.hide()
        self.settings_window.show()

if __name__ == "__main__":
    app = QApplication([])
    window = MyStartUpWindow()
    window.show()
    app.exec()

