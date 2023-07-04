import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from mainwindow import Ui_MainWindow
import yaml
import nidaqmx
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from nidaqmx.constants import AcquisitionType


def on_btn_start_clicked():  # start merania
    ui.btn_start.setEnabled(False)
    print("on_btn_start_clicked")
    global progress_sec
    global measure_time
    progress_sec = 1

    ui.label_progress.setText("Starting data collection")

    timer_thread = threading.Thread(target=start_timer, args=((measure_time+3),))
    ref_data_thread = threading.Thread(target=start_ref_sens_data_collection)

    timer_thread.start()
    ref_data_thread.start()

    timer_thread.join()
    ref_data_thread.join()

    # vytvorenie grafu
    plot_data()

def start_timer(duration):
    end_time = time.time() + duration
    print("start timer")
    while time.time() < end_time:
        time.sleep(1)
        update_progressBar()
def start_ref_sens_data_collection():
    from datetime import datetime

    with nidaqmx.Task() as task:
        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        task.ai_channels.add_ai_accel_chan(deviceName_channel, sensitivity=1.079511)

        # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
        task.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                        samps_per_chan=number_of_samples_per_channel)

        print("Start merania")
        current_time = datetime.now().time()
        time_string = current_time.strftime("%H:%M:%S.%f") # [:-2]
        start_time = time.time()
        # spustenie získavania vzoriek
        task.start()

        # čítam získane vzorky
        data = task.read(number_of_samples_per_channel=number_of_samples_per_channel,
                         timeout=nidaqmx.constants.WAIT_INFINITELY)

        end_time = time.time()

        # stop
        task.stop()
        print("Stop merania")

        # dĺžka merania
        elapsed_time = (end_time - start_time) * 1000
        print(f"Cas trvania merania: {elapsed_time:.2f} ms")

        # ulozenie dát do txt súboru
        save_data(data, time_string, elapsed_time)


def save_data(data, time_string, elapsed_time):
    from datetime import date

    today = date.today()
    date = today.strftime("%b-%d-%Y")
    os.makedirs(save_folder, exist_ok=True)

    file_path = os.path.join(save_folder, ref_name)

    with open(file_path, 'w') as file:
        file.write("# " + date + '\n')
        file.write("# " + time_string + '\n')
        file.write("# Dĺžka merania : " + str(measure_time) + "s (" + str(round(elapsed_time/1000,2)) + "s)" + '\n')
        file.write("# Vzorkovacia frekvencia : " + str(sample_rate) + '\n')
        file.write("# Počet vzoriek : " + str(number_of_samples_per_channel) + '\n')
        file.write("# Merane napätie :" + '\n')
        for item in data:
            file.write(str(item) + '\n')

    print("Zapisane do txt")

def plot_data():
    file_path = os.path.join(save_folder, ref_name)
    with open(file_path) as f:
        lines = (line for line in f if not line.startswith('#'))
        data = np.loadtxt(lines)

    sample_rate_sec = 1 / sample_rate

    plottime = np.arange(0, len(data) * sample_rate_sec, sample_rate_sec)

    plt.plot(plottime, data)

    plt.xlabel('Čas [s]')
    plt.ylabel('Napätie [V]')
    plt.title('Priebeh napätia')
    plt.grid(True)

    plt.show()

def update_progressBar():

    global progress_sec
    if progress_sec < measure_time:
        ui.label_progress.setText("Data collection")
        ui.progressBar.setValue(int(100 * progress_sec/measure_time))
    else:
        prog_finish = int(100 * progress_sec / measure_time)
        if prog_finish < 100:
            ui.progressBar.setValue(int(100 * progress_sec / measure_time))
        else :
            ui.progressBar.setValue(100)
            ui.label_progress.setText("Data collection FINISHED")
            if progress_sec > (measure_time+2):
                # timer.stop()
                ui.btn_start.setEnabled(True)
                text = ref_name + " saved"
                ui.label_progress.setText(text)
                ui.progressBar.setValue(0)

    progress_sec += 1

def on_btn_saveConfig_clicked():  # ulozenie configu
    print("on_btn_saveConfig_clicked")
    print(sample_rate)
    print(number_of_samples_per_channel)
    print(ref_name)
    print(save_folder)
    config['measurement']['sample_rate'] = sample_rate
    config['measurement']['number_of_samples_per_channel'] = number_of_samples_per_channel
    config['save_data']['ref_name'] = ref_name
    config['save_data']['destination_folder'] = save_folder

    with open('a_ref_config.yaml', 'w') as file:
        yaml.dump(config, file)

def on_toolBtn_selectFolder_clicked():  # vybratie priecinku
    print("on_toolBtn_selectFolder_clicked")
    global save_folder
    save_folder = QFileDialog.getExistingDirectory(window, "Select Save Folder")
    if save_folder:
        print("Save folder selected:", save_folder)
        ui.lineEdit_saveFolder.setText(save_folder)

def on_lineEdit_SampleRate_finished():
    text = ui.lineEdit_SampleRate.text()
    print("Text changed:", text)
    global number_of_samples_per_channel
    global measure_time
    global sample_rate
    print(int(text))
    sample_rate = int(text)
    number_of_samples_per_channel = int(measure_time*sample_rate)
    print(number_of_samples_per_channel)

def on_lineEdit_measure_finished():
    text = ui.lineEdit_measure.text()
    print("Text changed:", text)
    global number_of_samples_per_channel
    global measure_time
    global sample_rate
    measure_time = float(text)
    number_of_samples_per_channel = int(measure_time*sample_rate)
    print(number_of_samples_per_channel)

def on_lineEdit_saveFolder_finished():
    text = ui.lineEdit_saveFolder.text()
    print("Text changed: ", text)
    global save_folder
    save_folder = text

def on_lineEdit_fileName_finished():
    text = ui.lineEdit_file_name.text() + ".txt"
    print("Text changed: ", text)
    global ref_name
    ref_name = text


# otovríme config file
with open('a_ref_config.yaml', 'r') as file:
    config = yaml.safe_load(file)

sample_rate = config['measurement']['sample_rate']
number_of_samples_per_channel = config['measurement']['number_of_samples_per_channel']

deviceName_channel = config['device']['name'] + '/' + config['device']['channel']

ref_name = config['save_data']['ref_name']
save_folder = config['save_data']['destination_folder']
measure_time = number_of_samples_per_channel / sample_rate
progress_sec = 0
# timer = None
##

# vytvorenie class s ui elementmi
app = QApplication([])
window = QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(window)
##

# pociatocna init lineEditov
ui.lineEdit_SampleRate.setText(str(sample_rate))
ui.lineEdit_saveFolder.setText(save_folder)
ui.lineEdit_measure.setText(str(measure_time))
##

ui.progressBar.setValue(0)

# priradenie buttonom funkciu
ui.btn_start.clicked.connect(on_btn_start_clicked)
ui.btn_saveConfig.clicked.connect(on_btn_saveConfig_clicked)
ui.toolBtn_selectFolder.clicked.connect(on_toolBtn_selectFolder_clicked)
##

# priradenie lineEditom funkciu
ui.lineEdit_measure.editingFinished.connect(on_lineEdit_measure_finished)
ui.lineEdit_SampleRate.editingFinished.connect(on_lineEdit_SampleRate_finished)
ui.lineEdit_file_name.editingFinished.connect(on_lineEdit_fileName_finished)
ui.lineEdit_saveFolder.editingFinished.connect(on_lineEdit_saveFolder_finished)
##


window.show()
app.exec_()
