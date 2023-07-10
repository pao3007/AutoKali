import multiprocessing as mp
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from mainwindow import Ui_MainWindow
import yaml
import nidaqmx
import time
import os
import numpy as np
import matplotlib.pyplot as plt
from nidaqmx.constants import AcquisitionType

documents_path = os.path.expanduser('~/Documents')
main_folder_name = 'Sylex_sensors_export'
subfolder1a_name = 'reference'
subfolder2a_name = 'optical'
subfolder1b_name = 'reference_raw'
subfolder2b_name = 'optical_raw'

main_folder_path = os.path.join(documents_path, main_folder_name)
subfolder1a_path = os.path.join(main_folder_path, subfolder1a_name)
subfolder2a_path = os.path.join(main_folder_path, subfolder2a_name)
subfolder1raw_path = os.path.join(main_folder_path, subfolder1b_name)
subfolder2raw_path = os.path.join(main_folder_path, subfolder2b_name)

# otovríme config file
config_file_path = os.path.join(main_folder_path, 'a_ref_config.yaml')
with open(config_file_path, 'r') as file:
    config = yaml.safe_load(file)

sample_rate = config['ref_measurement']['sample_rate']
number_of_samples_per_channel = config['ref_measurement']['number_of_samples_per_channel']
deviceName_channel = config['device']['name'] + '/' + config['device']['channel']
ref_opt_name = config['save_data']['ref_name']
save_folder = config['save_data']['destination_folder']

measure_time = number_of_samples_per_channel / sample_rate
progress_sec = 0
refData = None
opt_sentinel_file_name = None

def on_btn_start_clicked():  # start merania
    ui.btn_start.setEnabled(False)
    print("on_btn_start_clicked")
    global progress_sec
    global measure_time
    progress_sec = 1

    start_sentinel()
    check_new_files()

    if __name__ == '__main__':
        mp.set_start_method('spawn')
        pool = mp.Pool()
        pool.map(start_ref_sens_data_collection)
        pool.map(start_timer, (measure_time+3))

        pool.close()
        pool.join()

    print("Start raw")
    make_opt_raw(4)

    # vytvorenie grafu
    # plot_data(refData)

def start_sentinel(): # ! vybrat path to .exe a project
    # global sentinel_app
    # global sentinel_project
    sentinel_app = r'C:\Users\lukac\Desktop\Sylex\Sentinel\Sentinel2_Dynamic_v0_4_1 (AE)\Sentinel2_Dynamic_v0_4_1'
    sentinel_project = 'test.ssd'

    os.chdir(sentinel_app)
    os.system("start ClientApp_Dyn " + sentinel_project)
    ui.label_progress.setText("Starting Sentinel-D")

def check_new_files():
    global opt_sentinel_file_name
    # Get the initial set of files in the folder
    initial_files = set(os.listdir(subfolder2a_path))

    while True:
        # Sleep for some time
        time.sleep(0.01)

        # Get the current set of files in the folder
        current_files = set(os.listdir(subfolder2a_path))

        # Find the difference between the current and initial files
        new_files = current_files - initial_files

        if new_files:
            for file in new_files:
                opt_sentinel_file_name = file
                print(opt_sentinel_file_name)
            break

def start_ref_sens_data_collection():
    from datetime import datetime
    app_name = "ClientApp_Dyn"

    with nidaqmx.Task() as task:
        # nazov zariadenia/channel, min/max value -> očakávané hodnoty v tomto rozmedzí
        task.ai_channels.add_ai_accel_chan(deviceName_channel, sensitivity=1000)


        # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
        task.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                                        samps_per_chan=number_of_samples_per_channel)

        # print("Start merania")
        current_time = datetime.now().time()
        time_string = current_time.strftime("%H:%M:%S.%f") # [:-2]
        start_time = time.time()
        # spustenie získavania vzoriek
        task.start()

        # čítam získane vzorky
        data = task.read(number_of_samples_per_channel=number_of_samples_per_channel,
                         timeout=nidaqmx.constants.WAIT_INFINITELY)

        end_time = time.time()

        os.system(f'taskkill /F /IM {app_name}.exe')

        # stop
        task.stop()
        # print("Stop merania")

        # dĺžka merania
        elapsed_time = (end_time - start_time) * 1000
        # print(f"Cas trvania merania: {elapsed_time:.2f} ms")

        # ulozenie dát do txt súboru
        save_data(data, time_string, elapsed_time)
        global refData
        refData = data

def start_timer(duration):
    end_time = time.time() + duration
    ui.label_progress.setText("Starting data collection")
    while time.time() < end_time:
        time.sleep(1)
        #QtTest.QTest.qWait(1000)
        update_progressBar()

def save_data(data, time_string, elapsed_time):
    from datetime import date

    today = date.today()
    date = today.strftime("%b-%d-%Y")

    file_path = os.path.join(subfolder1a_path, ref_opt_name)
    file_path_raw = os.path.join(subfolder1raw_path, ref_opt_name)

    with open(file_path, 'w') as file:
        file.write("# " + date + '\n')
        file.write("# " + time_string + '\n')
        file.write("# Dĺžka merania : " + str(measure_time) + "s (" + str(round(elapsed_time/1000, 2)) + "s)" + '\n')
        file.write("# Vzorkovacia frekvencia : " + str(sample_rate) + '\n')
        file.write("# Počet vzoriek : " + str(number_of_samples_per_channel) + '\n')
        file.write("# Merane napätie :" + '\n')
        for item in data:
            file.write(str(item) + '\n')

    with open(file_path_raw, 'w') as file:
        for item in data:
            file.write(str(item) + '\n')

    # print("Zapisane do txt")

def make_opt_raw(num_lines_to_skip):
    file_path = os.path.join(subfolder2a_path, opt_sentinel_file_name)
    file_path_raw = os.path.join(subfolder2raw_path, ref_opt_name)

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

    os.chdir(subfolder2a_path)

    if os.path.exists(ref_opt_name):
        os.remove(ref_opt_name)

    os.rename(opt_sentinel_file_name, ref_opt_name)

def plot_data(data):
    file_path = os.path.join(save_folder, ref_opt_name)
    # with open(file_path) as f:
    #     lines = (line for line in f if not line.startswith('#'))
    #     data = np.loadtxt(lines)


    sample_rate_sec = 1 / sample_rate

    plottime = np.arange(0, len(data) * sample_rate_sec, sample_rate_sec)

    plt.plot(plottime, data)

    plt.xlabel('Time [s]')
    plt.ylabel('Acceleration [g]')
    plt.title('Acceleration')
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
                text = ref_opt_name + " saved"
                ui.label_progress.setText(text)
                ui.progressBar.setValue(0)

    progress_sec += 1

def on_btn_saveConfig_clicked():  # ulozenie configu
    print("on_btn_saveConfig_clicked")
    print(sample_rate)
    print(number_of_samples_per_channel)
    print(ref_opt_name)
    print(save_folder)
    config['ref_measurement']['sample_rate'] = sample_rate
    config['ref_measurement']['number_of_samples_per_channel'] = number_of_samples_per_channel
    config['save_data']['ref_name'] = ref_opt_name
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
    text = ui.lineEdit_file_name.text() + ".csv"
    print("Text changed: ", text)
    global ref_opt_name
    ref_opt_name = text

def create_folders():

    # Check if the main folder already exists
    if not os.path.exists(main_folder_path):
        # Create the main folder
        os.makedirs(main_folder_path)
        print(f"Main folder created: {main_folder_path}")
    else:
        print(f"Main folder already exists: {main_folder_path}")

    # Create the subfolders inside the main folder
    os.makedirs(subfolder1a_path, exist_ok=True)
    os.makedirs(subfolder2a_path, exist_ok=True)
    print(f"Subfolder 1a created: {subfolder1a_path}")
    print(f"Subfolder 2a created: {subfolder2a_path}")

    os.makedirs(subfolder1raw_path, exist_ok=True)
    os.makedirs(subfolder2raw_path, exist_ok=True)
    print(f"Subfolder 1b created: {subfolder1raw_path}")
    print(f"Subfolder 2b created: {subfolder2raw_path}")

create_folders()

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
