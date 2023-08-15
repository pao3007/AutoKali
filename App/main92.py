import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
import PyQt5.QtCore
from mainwindow import Ui_MainWindow
from AC_calibration_1FBG_v3 import ACCalib_1ch
import yaml
import nidaqmx
import time
import os
from scipy.fft import fft
from nidaqmx.constants import AcquisitionType

class start_timer_thread(PyQt5.QtCore.QThread):
    progress_signal = PyQt5.QtCore.pyqtSignal(int)
    finished_signal = PyQt5.QtCore.pyqtSignal()
    def __init__(self, argument):
        super().__init__()
        self.duration = argument

    def run(self):
        kali.ui.label_progress.setText("Starting data collection")
        i = 1
        while i < self.duration:
            PyQt5.QtCore.QThread.msleep(1000)
            self.progress_signal.emit(i)
            i = i + 1
        self.finished_signal.emit()

class start_ref_sens_data_collection_thread(PyQt5.QtCore.QThread):
    finished_signal = PyQt5.QtCore.pyqtSignal()

    def run(self):
        kali.start_ref_sens_data_collection()
        self.finished_signal.emit()

class start_check_new_file_thread(PyQt5.QtCore.QThread):
    finished_signal = PyQt5.QtCore.pyqtSignal()

    def run(self):
        print("Start check thread")
        kali.check_new_files()
        self.finished_signal.emit()

class start_ref_check_sin_thread(PyQt5.QtCore.QThread):
    finished_signal = PyQt5.QtCore.pyqtSignal()

    def __init__(self, deviceName_channel):
        super().__init__()
        self.termination = False
        self.task_sin = nidaqmx.Task()
        self.deviceName_channel = deviceName_channel

    def run(self):
        sample_rate = 12800
        number_of_samples_per_channel = int(12800 / 3)
        sin_threshold = 0.004
        #
        print("Start ref sens sinus check")
        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        self.task_sin.ai_channels.add_ai_accel_chan(self.deviceName_channel, sensitivity=1000)

        # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
        self.task_sin.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)
        self.task_sin.start()

        ## 2 varianta
        while not self.termination:
            data = self.task_sin.read(number_of_samples_per_channel=number_of_samples_per_channel,
                                      timeout=nidaqmx.constants.WAIT_INFINITELY)
            if self.is_sinus2(data, sample_rate):  # self.is_sinus(data, sin_threshold):
                kali.ui.btn_start.setEnabled(True)
                print("REF IS READY \n")
            else:
                kali.ui.btn_start.setEnabled(False)
                print("INSTALL REF SENS \n")
        kali.ui.btn_start.setEnabled(False)
        self.task_sin.stop()

    def is_sinus(self, samples, threshold):
        # Perform frequency domain analysis using Fourier Transform (FFT)
        fft_values = np.fft.fft(samples)
        amplitudes = np.abs(fft_values)
        max_amplitude = np.max(amplitudes)

        # Calculate the normalized amplitude of the dominant frequency
        normalized_amplitude = max_amplitude / len(samples)

        # Check if the waveform is sinusoidal based on the threshold
        print(normalized_amplitude)
        if normalized_amplitude >= threshold:
            return True
        else:
            return False

    def is_sinus2(self, samples, sample_rate):
        # Perform Fast Fourier Transform
        data = np.array(samples)
        yf = fft(data)
        xf = np.linspace(0.0, 1.0 / (2.0 / sample_rate), len(data) // 2)

        # Check if the signal forms a periodic waveform
        # If there is a peak in the frequency domain, we can say that there is a periodic signal
        peak_threshold = 10  # adjust this threshold according to your needs
        peak_freqs = xf[np.abs(yf[:len(data) // 2]) > peak_threshold]
        if len(peak_freqs) > 0:
            return True
        else:
            return False

class autokali(PyQt5.QtCore.QObject):

    def __init__(self):
        super().__init__()
        self.ref_sensitivity = 1.079511
        self.GainMark = 150
        self.sensitivities_file = "sensitivities.csv"
        self.timecorrections_file = "time_corrections.csv"

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
        self.script_folder_path = os.getcwd()

        # otovríme config file
        config_file_path = os.path.join(self.main_folder_path, 'a_ref_config.yaml')
        with open(config_file_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.sample_rate = self.config['ref_measurement']['sample_rate']
        self.number_of_samples_per_channel = self.config['ref_measurement']['number_of_samples_per_channel']
        self.deviceName_channel = self.config['device']['name'] + '/' + self.config['device']['channel']
        self.ref_opt_name = self.config['save_data']['ref_name']
        self.save_folder = self.config['save_data']['destination_folder']

        self.measure_time = self.number_of_samples_per_channel / self.sample_rate
        self.refData = None
        self.opt_sentinel_file_name = None

        self.create_folders()

        self.window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

        # pociatocna init lineEditov
        self.ui.lineEdit_SampleRate.setText(str(self.sample_rate))
        self.ui.lineEdit_saveFolder.setText(self.save_folder)
        self.ui.lineEdit_measure.setText(str(self.measure_time))
        ##

        self.ui.progressBar.setValue(0)

        # priradenie buttonom funkciu
        self.ui.btn_start.clicked.connect(self.on_btn_start_clicked)
        self.ui.btn_saveConfig.clicked.connect(self.on_btn_saveConfig_clicked)
        self.ui.toolBtn_selectFolder.clicked.connect(self.on_toolBtn_selectFolder_clicked)
        ##

        # priradenie lineEditom funkciu
        self.ui.lineEdit_measure.editingFinished.connect(self.on_lineEdit_measure_finished)
        self.ui.lineEdit_SampleRate.editingFinished.connect(self.on_lineEdit_SampleRate_finished)
        self.ui.lineEdit_file_name.editingFinished.connect(self.on_lineEdit_fileName_finished)
        self.ui.lineEdit_saveFolder.editingFinished.connect(self.on_lineEdit_saveFolder_finished)
        ##

        self.ui.output_browser.setText("Calibration results : " + '\n' + "please install reference sensor")

        self.window.show()
        self.thread_check_sin = start_ref_check_sin_thread(self.deviceName_channel)
        self.thread_check_sin.start()

    def on_btn_start_clicked(self):  # start merania
        self.thread_check_sin.termination = True
        self.ui.btn_start.setEnabled(False)
        self.ui.label_progress.setText("Starting Sentinel-D")

        self.start_sentinel()

        self.thread_prog_bar = start_timer_thread((self.measure_time+4))
        self.thread_ref_sens = start_ref_sens_data_collection_thread()
        self.thread_check_new_file = start_check_new_file_thread()

        self.thread_prog_bar.finished_signal.connect(self.thread_prog_bar_finished)
        self.thread_prog_bar.progress_signal.connect(self.update_progressBar)
        self.thread_ref_sens.finished.connect(self.thread_ref_sens_finished)
        self.thread_check_new_file.finished.connect(self.thread_check_new_file_finished)

        self.thread_check_new_file.start()

    def thread_prog_bar_finished(self):
        self.ui.btn_start.setEnabled(True)
        self.thread_check_sin = start_ref_check_sin_thread(self.deviceName_channel)
        self.thread_check_sin.start()

    def thread_ref_sens_finished(self):
        self.make_opt_raw(4)
        acc_script = ACCalib_1ch(self.ref_opt_name[0:-4], self.script_folder_path, self.main_folder_path, self.subfolderOptRaw_path,
                                 self.subfolderRefRaw_path, self.ref_sensitivity, self.GainMark)

        acc_script.start(0)
        self.acc_kalib = acc_script.start(1)  # [0]>wavelength,[1]>sensitivity pm/g at gainMark,[2]>flatness_edge_l,
        # [3]>flatness_edge_r,[4]>sens. flatness,[5]>MAX acc,[6]>MIN acc,[7]>DIFF symmetry,[8]>TimeCorrection
        self.save_calib_data()

    def thread_check_new_file_finished(self):
        self.thread_prog_bar.start()
        self.thread_ref_sens.start()
        print("finito")

    def save_calib_data(self):
        self.passTest = "PASS/FAIL"
        file_path = os.path.join(self.subfolderCalibrationData, self.ref_opt_name)
        self.ui.output_browser.setText("Calibration results: " + '\n' + '\n' +
                                       "# S/N :" + '\t \t' + self.ref_opt_name + '\n' +
                                       "# Date :" + '\t \t' + self.current_date + '\n' +
                                       "# Time : " + '\t \t' + self.time_string + '\n' +
                                       "# Center wavelength : " + '\t \t' + str(self.acc_kalib[0]) + '\n' +
                                       "# Sensitivity : " + '\t \t' + str(self.acc_kalib[1]) + " pm/g at " + str(self.GainMark) + " Hz" + '\n' +
                                       "# Sensitivity flatness : " + '\t \t' + str(self.acc_kalib[4]) + " between " +
                                       str(self.acc_kalib[2]) + " Hz and " + str(self.acc_kalib[3]) + " Hz" + '\n' +
                                       "--------->" + self.passTest + "<---------")
        with open(file_path, 'w') as file:
            file.write("# S/N :" + '\n' + '\t' + "place holder" + '\n')
            file.write("# Date :" + '\n' + '\t' + self.current_date + '\n')
            file.write("# Time : " + '\n' + '\t' + self.time_string + '\n')
            file.write("# Center wavelength : " + '\n' + '\t' + str(self.acc_kalib[0]) + '\n')
            file.write("# Sensitivity : " + '\n' + '\t' + str(self.acc_kalib[1]) + " pm/g at " + str(self.GainMark) + " Hz" + '\n')
            file.write("# Sensitivity flatness : " + '\n' + '\t' + str(self.acc_kalib[4]) + " between " + str(self.acc_kalib[2]) + " Hz and " + str(self.acc_kalib[3]) + " Hz" + '\n')

        file_path = os.path.join(self.main_folder_path, self.sensitivities_file)
        if os.path.exists(file_path):
            os.remove(file_path)
        file_path = os.path.join(self.main_folder_path, self.timecorrections_file)
        if os.path.exists(file_path):
            os.remove(file_path)

    def start_sentinel(self):  # ! vybrat path to .exe a project

        sentinel_app = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1\Sentinel2_Dynamic_v0_4_1'
        sentinel_project = 'test.ssd'

        os.chdir(sentinel_app)
        os.system("start /min ClientApp_Dyn " + sentinel_project)

    def check_new_files(self):
        # Get the initial set of files in the folder
        initial_files = set(os.listdir(self.subfolderOpt_path))

        while True:

            # Get the current set of files in the folder
            current_files = set(os.listdir(self.subfolderOpt_path))

            # Find the difference between the current and initial files
            new_files = current_files - initial_files

            if new_files:
                for file in new_files:
                    self.opt_sentinel_file_name = file
                break

    def start_ref_sens_data_collection(self):
        # i = 0
        # while i < 5:
        #     PyQt5.QtCore.QThread.msleep(1000)
        #     print(i)
        #     i = i + 1

        from datetime import datetime
        app_name = "ClientApp_Dyn"

        with nidaqmx.Task() as task:
            # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
            task.ai_channels.add_ai_accel_chan(self.deviceName_channel, sensitivity=1000)


            # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
            task.timing.cfg_samp_clk_timing(self.sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                            samps_per_chan=self.number_of_samples_per_channel)

            print("Start merania")
            current_time = datetime.now().time()
            self.time_string = current_time.strftime("%H:%M:%S.%f")
            start_time = time.time()
            # spustenie získavania vzoriek
            task.start()

            # čítam získane vzorky
            data = task.read(number_of_samples_per_channel=self.number_of_samples_per_channel,
                             timeout=nidaqmx.constants.WAIT_INFINITELY)

            end_time = time.time()

            os.system(f'taskkill /F /IM {app_name}.exe')

            # stop
            task.stop()
            print("Stop merania")

            # dĺžka merania
            elapsed_time = (end_time - start_time) * 1000
            print(f"Cas trvania merania: {elapsed_time:.2f} ms")

            # ulozenie dát do txt súboru
            self.save_data(data, elapsed_time)
            self.refData = data

    def update_progressBar(self, value):

        progress_sec = value
        if progress_sec < self.measure_time:
            self.ui.label_progress.setText("Data collection")
            self.ui.progressBar.setValue(int(100 * progress_sec/self.measure_time))
        else:
            prog_finish = int(100 * progress_sec / self.measure_time)
            if prog_finish < 100:
                self.ui.progressBar.setValue(int(100 * progress_sec / self.measure_time))
            else :
                self.ui.progressBar.setValue(100)
                self.ui.label_progress.setText("Data collection FINISHED")
                if progress_sec > (self.measure_time+2):
                    text = self.ref_opt_name + " saved"
                    self.ui.label_progress.setText(text)
                    self.ui.progressBar.setValue(0)

    def save_data(self, data, elapsed_time):
        from datetime import date

        today = date.today()
        self.current_date = today.strftime("%b-%d-%Y")

        file_path = os.path.join(self.subfolderRef_path, self.ref_opt_name)
        file_path_raw = os.path.join(self.subfolderRefRaw_path, self.ref_opt_name)

        with open(file_path, 'w') as file:
            file.write("# " + self.current_date + '\n')
            file.write("# " + self.time_string + '\n')
            file.write("# Dĺžka merania : " + str(self.measure_time) + "s (" + str(round(elapsed_time/1000, 2)) + "s)" + '\n')
            file.write("# Vzorkovacia frekvencia : " + str(self.sample_rate) + '\n')
            file.write("# Počet vzoriek : " + str(self.number_of_samples_per_channel) + '\n')
            file.write("# Merane zrýchlenie :" + '\n')
            for item in data:
                file.write(str(item) + '\n')

        with open(file_path_raw, 'w') as file:
            for item in data:
                file.write(str(item) + '\n')

        print("Zapisane do txt")

    def make_opt_raw(self, num_lines_to_skip):
        file_path = os.path.join(self.subfolderOpt_path, self.opt_sentinel_file_name)
        file_path_raw = os.path.join(self.subfolderOptRaw_path, self.ref_opt_name)

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

        os.chdir(self.subfolderOpt_path)

        if os.path.exists(self.ref_opt_name):
            os.remove(self.ref_opt_name)

        os.rename(self.opt_sentinel_file_name, self.ref_opt_name)

    def on_btn_saveConfig_clicked(self):  # ulozenie configu
        print("on_btn_saveConfig_clicked")
        print(self.sample_rate)
        print(self.number_of_samples_per_channel)
        print(self.ref_opt_name)
        print(self.save_folder)
        self.config['ref_measurement']['sample_rate'] = self.sample_rate
        self.config['ref_measurement']['number_of_samples_per_channel'] = self.number_of_samples_per_channel
        self.config['save_data']['ref_name'] = self.ref_opt_name
        self.config['save_data']['destination_folder'] = self.save_folder

        with open('a_ref_config.yaml', 'w') as file:
            yaml.dump(self.config, file)

    def on_toolBtn_selectFolder_clicked(self):  # vybratie priecinku
        print("on_toolBtn_selectFolder_clicked")
        self.save_folder = QFileDialog.getExistingDirectory(self.window, "Select Save Folder")
        if self.save_folder:
            print("Save folder selected:", self.save_folder)
            self.ui.lineEdit_saveFolder.setText(self.save_folder)

    def on_lineEdit_SampleRate_finished(self):
        text = self.ui.lineEdit_SampleRate.text()
        print("Text changed:", text)
        print(int(text))
        self.sample_rate = int(text)
        self.number_of_samples_per_channel = int(self.measure_time*self.sample_rate)
        print(self.number_of_samples_per_channel)

    def on_lineEdit_measure_finished(self):
        text = self.ui.lineEdit_measure.text()
        print("Text changed:", text)
        self.measure_time = float(text)
        self.number_of_samples_per_channel = int(self.measure_time*self.sample_rate)
        print(self.number_of_samples_per_channel)

    def on_lineEdit_saveFolder_finished(self):
        text = self.ui.lineEdit_saveFolder.text()
        print("Text changed: ", text)
        self.save_folder = text

    def on_lineEdit_fileName_finished(self):
        text = self.ui.lineEdit_file_name.text() + ".csv"
        print("Text changed: ", text)
        self.ref_opt_name = text

    def create_folders(self):

        # Check if the main folder already exists
        if not os.path.exists(self.main_folder_path):
            # Create the main folder
            os.makedirs(self.main_folder_path)
            print(f"Main folder created: {self.main_folder_path}")
        else:
            print(f"Main folder already exists: {self.main_folder_path}")

        # Create the subfolders inside the main folder
        os.makedirs(self.subfolderRef_path, exist_ok=True)
        os.makedirs(self.subfolderOpt_path, exist_ok=True)
        os.makedirs(self.subfolderRefRaw_path, exist_ok=True)
        os.makedirs(self.subfolderOptRaw_path, exist_ok=True)
        os.makedirs(self.subfolderCalibrationData, exist_ok=True)


if __name__ == "__main__":
    # vytvorenie class s ui elementmi
    app = QApplication([])
    kali = autokali()

    app.exec_()
