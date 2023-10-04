from PyQt5.QtCore import QObject, pyqtSignal
from nidaqmx.constants import WAIT_INFINITELY
from definitions import kill_sentinel, start_sentinel_modbus
from acc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from MyStartUpWindow import MyStartUpWindow
from os import path as os_path, remove as os_remove, rename as os_rename, chdir as os_chdir
from time import time as time_time, sleep as time_sleep
from datetime import datetime, date
from acc.SettingsParams import MySettings
from multiprocessing import Process, Manager


class SignalEmitter(QObject):
    process_finished = pyqtSignal()


class ThreadRefSensDataCollectionWithProcess:

    def __init__(self, window: MyStartUpWindow, thcfgs: ThreadControlFuncGenStatements, s_n: str, 
                 my_settings: MySettings, s_n_export: str):
        super().__init__()
        manager = Manager()
        self.shared_dict = manager.dict()
        self.signal_emitter = SignalEmitter()

        self.shared_dict['s_n_export'] = s_n_export
        self.shared_dict['opt_time'] = None
        self.shared_dict['out'] = None
        self.shared_dict['time_string'] = None
        self.shared_dict['current_date'] = None
        self.shared_dict['time_stamp'] = None
        self.shared_dict['task'] = None
        self.shared_dict['thcfgs'] = thcfgs
        self.shared_dict['my_settings'] = my_settings
        self.shared_dict['window'] = window
        self.shared_dict['s_n'] = s_n
        self.shared_dict['acc_calib'] = None
        self.shared_dict['num_of_samples_per_cycle'] = int(my_settings.ref_sample_rate / 10)
        self.process = Process(target=self.start_ref_sens_data_collection)
        # Start the data collection function in a separate process

    def run(self):
        self.process.start()

    def start_ref_sens_data_collection(self):
        s_n_export = self.shared_dict['s_n_export']
        thcfgs = self.shared_dict['thcfgs']
        my_settings = self.shared_dict['my_settings'] 
        window = self.shared_dict['window']
        # spustenie získavania vzoriek
        self.shared_dict['task'].start()
        print("Start merania")
        current_time = datetime.now().time()
        self.shared_dict['time_string'] = current_time.strftime("%H:%M:%S.%f")
        start_time = time_time()

        # čítam získane vzorky
        # data = self.shared_dict['task'].read(number_of_samples_per_channel=my_settings.ref_number_of_samples,
        #                       timeout=float(my_settings.generator_sweep_time+10))
        data = []
        try:
            while len(data) < my_settings.ref_number_of_samples and not thcfgs.get_emergency_stop():
                data.extend(self.shared_dict['task'].read(number_of_samples_per_channel=self.shared_dict['num_of_samples_per_cycle'],
                                  timeout=WAIT_INFINITELY))
        except Exception:
            thcfgs.set_emergency_stop(True)
            time_sleep(0.1)

        end_time = time_time()
        self.shared_dict['task'].close()
        thcfgs.set_finished_measuring(True)
        kill_sentinel(True, False)
        if thcfgs.get_emergency_stop():
            self.signal_emitter.process_finished.emit()
            return

        # stop
        # task.close()
        print("Stop merania")

        # dĺžka merania
        elapsed_time = (end_time - start_time) * 1000

        # ulozenie dát do txt súboru
        # self.save_data(data, elapsed_time)
        self.save_data(data, elapsed_time, my_settings)        # self.refData = data
        start_sentinel_modbus(my_settings.folder_sentinel_modbus_folder,
                              my_settings.subfolder_sentinel_project,
                              my_settings.opt_project, my_settings.opt_channels)
        self.thread_ref_sens_finished(s_n_export, thcfgs, my_settings, window)

    def save_data(self, data, elapsed_time, my_settings):

        today = date.today()
        self.shared_dict['current_date'] = today.strftime("%b-%d-%Y")

        file_path = os_path.join(my_settings.folder_ref_export, self.shared_dict['s_n'] + '.csv')
        file_path_raw = os_path.join(my_settings.folder_ref_export_raw, self.shared_dict['s_n'] + '.csv')
        with open(file_path, 'w') as file:
            file.write("# " + self.shared_dict['current_date'] + '\n')
            file.write("# " + self.shared_dict['time_string'] + '\n')
            file.write(
                "# Dĺžka merania : " + str(my_settings.ref_measure_time) + "s (" + str(round(elapsed_time / 1000, 2)) +
                "s)" + '\n')
            file.write("# Vzorkovacia frekvencia : " + str(my_settings.ref_sample_rate) + '\n')
            file.write("# Počet vzoriek : " + str(my_settings.ref_number_of_samples) + '\n')
            file.write("# Merane zrýchlenie :" + '\n')
            for item in data:
                file.write(str(item) + '\n')

        with open(file_path_raw, 'w') as file:
            for item in data:
                file.write(str(item) + '\n')

        print("Zapisane do txt")

    def thread_ref_sens_finished(self, s_n_export, thcfgs, my_settings, window):
        print("CALIBRATION --------------->")
        if not thcfgs.get_emergency_stop():
            self.make_opt_raw(4, my_settings, window)
            time_format = "%H:%M:%S.%f"
            opt = datetime.strptime(self.shared_dict['opt_time'], time_format)
            ref = datetime.strptime(self.shared_dict['time_string'], time_format)
            time_difference = opt - ref
            time_difference = time_difference.total_seconds()

            file_path = os_path.join(my_settings.folder_main, "sensitivities.csv")
            if os_path.exists(file_path):
                os_remove(file_path)
            file_path = os_path.join(my_settings.folder_main, "time_corrections.csv")
            if os_path.exists(file_path):
                os_remove(file_path)
            if my_settings.opt_channels == 1:
                from acc.AC_calibration_1FBG_v3 import ACCalib_1ch
                self.shared_dict['out'] = ACCalib_1ch(self.shared_dict['s_n'], window.starting_folder, my_settings.folder_main,
                                       my_settings.folder_opt_export_raw,
                                       my_settings.folder_ref_export_raw,
                                       float(my_settings.calib_reference_sensitivity),
                                       int(my_settings.calib_gain_mark),
                                       int(my_settings.opt_sampling_rate),
                                       int(my_settings.ref_sample_rate),
                                       my_settings.calib_filter_data,
                                       int(my_settings.calib_downsample),
                                       int(my_settings.calib_do_spectrum),
                                       int(my_settings.calib_l_flatness),
                                       int(my_settings.calib_r_flatness),
                                       int(my_settings.calib_angle_set_freq),
                                       int(my_settings.calib_phase_mark)).start(False,
                                                                                my_settings.calib_optical_sensitivity / 1000,
                                                                                True, time_difference)
                self.shared_dict['acc_calib'] = self.shared_dict['out'][0]
                self.shared_dict['out'] = ACCalib_1ch(self.shared_dict['s_n'], window.starting_folder, my_settings.folder_main,
                                       my_settings.folder_opt_export_raw,
                                       my_settings.folder_ref_export_raw,
                                       float(my_settings.calib_reference_sensitivity),
                                       int(my_settings.calib_gain_mark),
                                       int(my_settings.opt_sampling_rate),
                                       int(my_settings.ref_sample_rate),
                                       my_settings.calib_filter_data,
                                       int(my_settings.calib_downsample),
                                       int(my_settings.calib_do_spectrum),
                                       int(my_settings.calib_l_flatness),
                                       int(my_settings.calib_r_flatness),
                                       int(my_settings.calib_angle_set_freq),
                                       int(my_settings.calib_phase_mark)).start(my_settings.calib_plot,
                                                                                self.shared_dict['acc_calib'][1] / 1000,
                                                                                True, time_difference + self.shared_dict['acc_calib'][8])
                self.shared_dict['acc_calib'] = self.shared_dict['out'][0]
                # [0]>wavelength 1,[1]>sensitivity pm/g at gainMark,[2]>flatness_edge_l,
                # [3]>flatness_edge_r,[4]>sens. flatness,[5]>MAX acc,[6]>MIN acc,[7]>DIFF symmetry,[8]>TimeCorrection,
                # [9]>wavelength 2
            elif my_settings.opt_channels == 2:
                from acc.AC_calibration_2FBG_edit import ACCalib_2ch

                self.shared_dict['out'] = ACCalib_2ch(self.shared_dict['s_n'], window.starting_folder, my_settings.folder_main,
                                       my_settings.folder_opt_export_raw, my_settings.folder_ref_export_raw,
                                       float(my_settings.calib_reference_sensitivity), int(my_settings.calib_gain_mark),
                                       int(my_settings.opt_sampling_rate),
                                       int(my_settings.ref_sample_rate), my_settings.calib_filter_data,
                                       int(my_settings.calib_downsample),
                                       int(my_settings.calib_do_spectrum),
                                       int(my_settings.calib_l_flatness),
                                       int(my_settings.calib_r_flatness), int(my_settings.calib_angle_set_freq),
                                       int(my_settings.calib_phase_mark)).start(False,
                                                                                my_settings.calib_optical_sensitivity / 1000,
                                                                                True, 0)
                self.shared_dict['acc_calib'] = self.shared_dict['out'][0]
                self.shared_dict['out'] = ACCalib_2ch(self.shared_dict['s_n'], window.starting_folder, my_settings.folder_main,
                                       my_settings.folder_opt_export_raw, my_settings.folder_ref_export_raw,
                                       float(my_settings.calib_reference_sensitivity), int(my_settings.calib_gain_mark),
                                       int(my_settings.opt_sampling_rate),
                                       int(my_settings.ref_sample_rate), my_settings.calib_filter_data,
                                       int(my_settings.calib_downsample),
                                       int(my_settings.calib_do_spectrum),
                                       int(my_settings.calib_l_flatness),
                                       int(my_settings.calib_r_flatness), int(my_settings.calib_angle_set_freq),
                                       int(my_settings.calib_phase_mark)).start(my_settings.calib_plot,
                                                                                self.shared_dict['acc_calib'][1] / 1000,
                                                                                True, self.shared_dict['acc_calib'][8])
                self.shared_dict['acc_calib'] = self.shared_dict['out'][0]

                # [3]>flatness_edge_r,[4]>sens. flatness,[5]>MAX acc,[6]>MIN acc,[7]>DIFF symmetry,[8]>TimeCorrection,
                # [9]>wavelength 2
            self.shared_dict['time_stamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_calib_data(s_n_export, my_settings)

    def save_calib_data(self, s_n_export, my_settings):
        file_path = os_path.join(my_settings.folder_calibration_export, self.shared_dict['s_n'] + '.csv')
        with open(file_path, 'w') as file:
            file.write("# S/N :" + '\n' + '\t\t' + str(s_n_export) + '\n')
            file.write("# Time stamp: " + '\n' + '\t\t' + self.shared_dict['time_stamp'] + '\n')
            if len(self.shared_dict['acc_calib']) <= 9:
                file.write("# Channels : " + '\n' + '\t\t' "1" + '\n')
                file.write("# Center wavelength : " + '\n' + '\t\t' + str(self.shared_dict['acc_calib'][0]) + '\n')
            else:
                file.write("# Channels : " + '\n' + '\t\t' "2 \n")
                file.write("# Center wavelength : " + '\n' + '\t\t' + str(self.shared_dict['acc_calib'][0]) + ';' +
                           str(self.shared_dict['acc_calib'][9]) + '\n')
            file.write("# Sensitivity : " + '\n' + '\t\t' + str(self.shared_dict['acc_calib'][1]) + " pm/g at " + str(
                my_settings.calib_gain_mark) + " Hz" + '\n')
            file.write("# Sensitivity flatness : " + '\n' + '\t\t' + str(self.shared_dict['acc_calib'][4]) + " between " + str(
                self.shared_dict['acc_calib'][2]) + " Hz and " + str(self.shared_dict['acc_calib'][3]) + " Hz" + '\n')
            file.write("# Difference in symmetry : " + '\n' + '\t\t' + str(self.shared_dict['acc_calib'][7]) + " % " + '\n')
        self.signal_emitter.process_finished.emit()

    def make_opt_raw(self, num_lines_to_skip, my_settings, window):
        opt_sentinel_file_name = window.calib_window.autoCalib.opt_sentinel_file_name
        # print(str(my_settings.folder_opt_export) + "or\n" + str(self.opt_sentinel_file_name))
        file_path = os_path.join(my_settings.folder_opt_export, opt_sentinel_file_name)
        file_path_raw = os_path.join(my_settings.folder_opt_export_raw, self.shared_dict['s_n'] + '.csv')

        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith(": Start Time:"):
                    # Remove ': Start Time:' part and strip leading and trailing whitespaces
                    full_time_string = line.replace(": Start Time:", "").strip()

                    # Extract only the time from the full datetime string
                    try:
                        # Try to parse the full datetime string
                        datetime_obj = datetime.strptime(full_time_string, "%Y.%m.%d %H:%M:%S.%f")
                        self.shared_dict['opt_time'] = datetime_obj.strftime("%H:%M:%S.%f")
                        break
                    except ValueError:
                        pass

            file.seek(0)

            total_lines = sum(1 for line in file)

            # Reset the file pointer to the beginning
            file.seek(0)

            # Skip the specified number of lines
            for _ in range(num_lines_to_skip):
                next(file)

            # Initialize the extracted columns list
            extracted_columns = []

            # Determine the number of lines to read (excluding the last line)
            lines_to_read = total_lines - num_lines_to_skip - 1  # int(window.my_settings.opt_sampling_rate*0.15)

            for _ in range(lines_to_read):
                line = file.readline()
                columns = line.strip().split(';')

                if my_settings.opt_channels == 1 and len(columns) >= 3:
                    extracted_columns.append(columns[2].lstrip())
                elif my_settings.opt_channels == 2 and len(columns) >= 4:
                    extracted_columns.append(columns[2].lstrip() + ' ' + columns[3].lstrip())

        with open(file_path_raw, 'w') as output_file:
            output_file.write('\n'.join(extracted_columns))

        os_chdir(my_settings.folder_opt_export)

        if os_path.exists(self.shared_dict['s_n'] + '.csv'):
            os_remove(self.shared_dict['s_n'] + '.csv')

        os_rename(opt_sentinel_file_name, self.shared_dict['s_n'] + '.csv')
