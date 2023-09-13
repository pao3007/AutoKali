from numpy import abs as np_abs
import win32api
import win32con
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QDesktopWidget, QDialog, QVBoxLayout, QLabel, \
    QLineEdit, QDialogButtonBox
from PyQt5.QtCore import QThread, QEvent, Qt
from os import chdir as os_chdir, path as os_path, remove as os_remove

from matplotlib import pyplot as plt
from definitions import (kill_sentinel, start_sentinel_modbus, start_sentinel_d, scale_app, center_on_screen,
                         load_all_config_files, set_wavelengths, get_params, copy_files, save_statistics_to_csv)
from MySettingsWindow import MySettingsWindow
from matplotlib.pyplot import close as pyplot_close
import ctypes
from ctypes import wintypes, byref as ctypes_byref
from SettingsParams import MySettings
from ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from re import search as re_search
from DatabaseCom import DatabaseCom


class MyMainWindow(QMainWindow):
    from MyStartUpWindow import MyStartUpWindow

    def __init__(self, window: MyStartUpWindow, my_settings: MySettings, thcfgs: ThreadControlFuncGenStatements):
        super().__init__()
        self.block_write = False
        self.s_n_export = None
        self.opt_force = False
        self.sensor_gen_error = False
        from autoCalibration import Ui_AutoCalibration

        self.thcfgs = thcfgs
        self.my_settings = my_settings
        self.window = window
        self.out_bro = 0
        self.sensor_gen_check = True
        self.thread_check_new_file = None
        self.config_file_path = None
        self.config_file = None
        self.settings_window = None
        self.measure = False
        self.s_n = None
        self.check_cnt = 0
        self.ref_init = 0
        self.remaining_time = 3
        self.sensor_ref_check = -1
        self.sensor_opt_check = -1

        self.ui = Ui_AutoCalibration()
        self.ui.setupUi(self)

        self.ui.just_box_6.setEnabled(False)
        self.ui.just_box_7.setEnabled(False)

        # open_action = QAction("Options", self)
        # open_action.triggered.connect(self.open_settings_window)
        # self.ui.menuSettings.addAction(open_action)
        self.autoCalib = AutoCalibMain(self, self.my_settings, self.thcfgs)

        self.ui.logo_label.setPixmap(QPixmap("images/logo.png"))

        self.ui.S_N_line.editingFinished.connect(self.set_s_n)

        self.ui.S_N_line.setPlaceholderText("Scan barcode or input SN...")

        self.ui.start_btn.clicked.connect(self.autoCalib.on_btn_start_clicked)
        self.ui.stop_btn.clicked.connect(self.emergency_stop_clicked)
        self.ui.plot_graph_check.stateChanged.connect(self.plot_check_changed)
        self.ui.select_config.currentTextChanged.connect(self.config_changed)
        self.ui.btn_load_wl.clicked.connect(self.btn_connect_load_wl)
        self.ui.btn_settings.clicked.connect(self.open_settings_window)
        self.ui.export_pass_btn.clicked.connect(self.exp_btn_clicked)
        self.ui.export_fail_btn.clicked.connect(self.exp_btn_clicked)
        self.ui.export_fail_btn.installEventFilter(self)
        self.ui.export_pass_btn.installEventFilter(self)

        self.ui.menuOperator.setTitle(f"Operator: {self.window.operator}")
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

        if my_settings is None or my_settings.check_if_none():
            self.ui.output_browser_3.setText("Restart APP, error while loading settings")

        self.ui.stop_btn.setHidden(True)
        self.ui.gen_status_label.setHidden(False)
        self.ui.gen_status_label_2.setHidden(True)
        self.change_sens_type_label()
        self.setWindowIcon(QIcon('images/logo_icon.png'))
        icon = QIcon(QPixmap("images/unlock.png"))
        self.ui.btn_opt_unlocked.setIcon(icon)
        self.ui.btn_opt_unlocked.setIconSize(self.ui.btn_opt_unlocked.sizeHint())
        self.ui.btn_opt_unlocked.setStyleSheet("background: transparent; border: none; text-align: center;")
        self.ui.btn_opt_unlocked.clicked.connect(self.opt_sens_is_already_unlocked)
        self.ui.btn_opt_unlocked.setHidden(True)

        icon = QIcon(QPixmap("images/setting_btn.png"))
        self.ui.btn_settings.setIcon(icon)
        self.ui.btn_settings.setIconSize(self.ui.btn_opt_unlocked.size())
        self.ui.btn_settings.setStyleSheet("background: transparent; border: none; text-align: center;")
        self.setFixedSize(self.width(), int(self.height() * 1))

        scale_app(self, self.window.window_scale)
        self.prev_opt_channel = self.my_settings.opt_channels
        # Load the User32.dll
        user32 = ctypes.WinDLL('user32', use_last_error=True)

        # Declare the Windows API methods
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        user32.GetKeyboardLayout.restype = wintypes.HKL

        def get_current_keyboard_layout():
            hwnd = user32.GetForegroundWindow()
            thread_id, process_id = wintypes.DWORD(), wintypes.DWORD()
            thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes_byref(process_id))
            hkl = user32.GetKeyboardLayout(thread_id)
            hkl_hex = hex(hkl & 0xFFFF)
            layout_id = f"0000{hkl_hex[2:]}".zfill(8)
            return layout_id

        self.native_keyboard_layout = get_current_keyboard_layout()
        if not win32api.LoadKeyboardLayout('00000409', win32con.KLF_ACTIVATE):
            self.ui.output_browser_3.setText("Please install US English keyboard layout so bar code scanners can work "
                                             "properly, then manually switch to US English layout or restart app.")

        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress and not self.isHidden() and not self.ui.S_N_line.hasFocus()
                and not self.block_write):
            # Manually updating QLineEdit
            current_text = self.ui.S_N_line.text()
            if event.key() == Qt.Key_Backspace:
                new_text = current_text[:-1]  # Remove the last character
            else:
                new_text = current_text + event.text()
            self.set_s_n(new_text)
            return True  # Event was handled

        if obj == self.ui.export_pass_btn and self.ui.fail_status_label.text() == "NOTE":
            if event.type() == QEvent.Enter:
                self.ui.fail_status_label.setStyleSheet("color: black;")
                return True
            elif event.type() == QEvent.Leave:
                self.ui.fail_status_label.setStyleSheet("color: grey;")
                return True
        elif obj == self.ui.export_fail_btn and self.ui.pass_status_label.text() == "EXPORT":
            if event.type() == QEvent.Enter:
                self.ui.pass_status_label.setStyleSheet("color: black;")
                return True
            elif event.type() == QEvent.Leave:
                self.ui.pass_status_label.setStyleSheet("color: grey;")
                return True
        return super().eventFilter(obj, event)

    def exp_btn_clicked(self):
        self.block_write = True
        dialog = QDialog(self)
        dialog.setWindowTitle("Export calibration" if not self.autoCalib.export_status else "Add note")

        dialog_layout = QVBoxLayout()

        label = QLabel("Do you want to add note?")
        dialog_layout.addWidget(label)

        text_input = QLineEdit()
        dialog_layout.addWidget(text_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)

        dialog.setLayout(dialog_layout)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.autoCalib.export_to_database(text_input.text(), True)
        self.block_write = False

    def opt_sens_is_already_unlocked(self):
        self.opt_force = True

    def plot_check_changed(self, state):
        try:
            # self.calib_figure.hide()
            pyplot_close('all')
        except:
            pass
        if state == 2:
            self.my_settings.calib_plot = True
            if self.autoCalib.calib_output:
                self.autoCalib.plot_graphs(self.autoCalib.calib_output)
        else:

            self.my_settings.calib_plot = False
        self.my_settings.save_config_file(True, self.window.config_file_path)

    def write_to_output_browser(self, text):
        self.out_bro += 1
        i = 0

        if (self.out_bro % 15) == 0:
            tmp = self.out_bro / 15
            while i < tmp:
                text += "."
                i += 1
            if tmp >= 3:
                self.out_bro = 0
            self.ui.output_browser_3.setText(text)
        elif self.out_bro == 0:
            self.ui.output_browser_3.setText(text)

    def change_sens_type_label(self):
        self.ui.label_opt_sens_type_label.setText(self.my_settings.opt_sensor_type + "\'s")

    def emergency_stop_clicked(self):
        print("STOP")
        self.ui.output_browser_3.setText("EMERGENCY STOP ENGAGED")
        self.thcfgs.set_emergency_stop(True)
        kill_sentinel(True, False)
        self.measure = False

    def first_sentinel_start(self):
        from ThreadSentinelCheckNewFile import ThreadSentinelCheckNewFile
        start_sentinel_d(self.my_settings.opt_project, self.my_settings.folder_sentinel_D_folder)
        self.thread_check_new_file = ThreadSentinelCheckNewFile(self.my_settings.folder_opt_export)
        self.thread_check_new_file.finished.connect(self.start_modbus)
        self.thread_check_new_file.start()

    def start_modbus(self):
        opt_sentinel_file_name = self.thread_check_new_file.opt_sentinel_file_name
        kill_sentinel(True, False)
        QThread.msleep(100)
        start_sentinel_modbus(self.my_settings.folder_sentinel_modbus_folder,
                              self.my_settings.folder_sentinel_D_folder,
                              self.my_settings.opt_project, self.my_settings.opt_channels)

        os_chdir(self.my_settings.folder_opt_export)

        if os_path.exists(opt_sentinel_file_name + '.csv'):
            os_remove(opt_sentinel_file_name + '.csv')
        QThread.msleep(100)
        self.show()
        self.window.hide()
        QThread.msleep(100)

        self.autoCalib.start()

    def opt_emit(self, is_ready):
        self.sensor_opt_check = is_ready

    def gen_emit(self, is_ready):
        self.sensor_gen_check = is_ready

    def ref_emit(self, is_ready):
        self.sensor_ref_check = is_ready

    def gen_error_emit(self, is_error):
        self.sensor_gen_error = is_error

    def update_wl_values(self, text):
        self.ui.opt_value_wl_label.setText(text)

    def update_ref_value(self, text):
        self.ui.ref_value_max_g_label.setText(text)

    def check_sensors_ready(self, check_status):
        if self.my_settings.opt_channels != 0 and self.ui.S_N_line.text().strip():
            if self.my_settings.opt_channels >= 2 and self.ui.start_btn.isEnabled():
                self.ui.btn_load_wl.setEnabled(True)
            else:
                self.ui.btn_load_wl.setEnabled(False)
            # print(str(self.sensor_opt_check) + " | " + str(self.sensor_ref_check) + " | " + str(self.sensor_gen_check) +
            #                                  " | " + str(self.measure))
            if self.sensor_opt_check == 1 and self.sensor_ref_check == 1 and self.sensor_gen_check and not self.measure and not self.sensor_gen_error:
                self.ui.start_btn.setEnabled(True)
            else:
                self.ui.start_btn.setEnabled(False)
        else:
            self.ui.start_btn.setEnabled(False)
            self.ui.btn_load_wl.setEnabled(False)
        if self.sensor_ref_check == 2 and (self.sensor_opt_check == 5 or self.opt_force):
            # print("TERMINATION ------------------------")
            self.autoCalib.thread_check_sin_opt.termination = True
            self.autoCalib.thread_check_sin_ref.termination = True
            self.sensor_ref_check = 2
            self.sensor_opt_check = 5

        if check_status or (self.sensor_ref_check == 2 and (self.sensor_opt_check == 5 or self.opt_force)):
            if self.sensor_opt_check != 0:
                if self.sensor_opt_check == 1 or self.sensor_opt_check == 11:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    self.ui.opt_sens_status_label.setText("OPT. SENSOR IS CONNECTED")
                    self.ui.opt_sens_status_label.setStyleSheet("color: blue;")
                elif self.sensor_opt_check == 3:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    self.ui.opt_sens_status_label.setText("OPT. USB DEVICE DISCONNECTED!")
                    if self.ui.opt_sens_status_label.isEnabled():
                        self.ui.opt_sens_status_label.setStyleSheet("color: red;")
                        self.ui.opt_sens_status_label.setEnabled(False)
                    else:
                        self.ui.opt_sens_status_label.setStyleSheet("color: black;")
                        self.ui.opt_sens_status_label.setEnabled(True)
                elif self.sensor_opt_check == 4 and not self.opt_force:
                    if self.my_settings.opt_channels == 2:
                        self.ui.btn_opt_unlocked.setHidden(False)
                        self.check_cnt += 1
                        if self.ui.opt_sens_status_label.isEnabled() and self.check_cnt >= 3:
                            self.ui.opt_sens_status_label.setText("OPT. SENSOR IS NOT READY")
                            self.ui.opt_sens_status_label.setStyleSheet("color: red;")
                            self.ui.opt_sens_status_label.setEnabled(False)
                            self.check_cnt = 0
                        elif self.check_cnt >= 3:
                            self.ui.opt_sens_status_label.setText("PLEASE UNLOCK THE SENSOR")
                            self.ui.opt_sens_status_label.setStyleSheet("color: red;")
                            self.ui.opt_sens_status_label.setEnabled(True)
                            self.check_cnt = 0
                    else:
                        self.ui.opt_sens_status_label.setText("OPT. SENSOR IS NOT READY")
                        self.ui.opt_sens_status_label.setStyleSheet("color: red;")
                elif self.sensor_opt_check == 5 or self.opt_force:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    self.ui.opt_sens_status_label.setText("OPT. SENSOR IS READY")
                    self.ui.opt_sens_status_label.setStyleSheet("color: green;")
                elif self.sensor_opt_check == 10:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    if self.my_settings.opt_channels == 2:
                        self.check_cnt += 1
                        if self.ui.opt_sens_status_label.isEnabled() and self.check_cnt >= 3:
                            self.ui.opt_sens_status_label.setText("OPT. SENSOR IS CONNECTED")
                            self.ui.opt_sens_status_label.setStyleSheet("color: orange;")
                            self.ui.opt_sens_status_label.setEnabled(False)
                            self.check_cnt = 0
                        elif self.check_cnt >= 3:
                            self.ui.opt_sens_status_label.setText("LOAD PROPER WAVELENGTHS")
                            self.ui.opt_sens_status_label.setStyleSheet("color: orange;")
                            self.ui.opt_sens_status_label.setEnabled(True)
                            self.check_cnt = 0
                    else:
                        self.ui.btn_opt_unlocked.setHidden(True)
                        self.ui.opt_sens_status_label.setText("OPT. SENSOR IS DISCONNECTED")
                        self.ui.opt_sens_status_label.setStyleSheet("color: orange;")
                elif self.sensor_opt_check == -1:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    self.ui.opt_sens_status_label.setText("OPT. SENSOR INITIALIZATION")
                    self.ui.opt_sens_status_label.setStyleSheet("color: black;")
            else:
                if self.my_settings.opt_channels == 2:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    self.check_cnt += 1
                    if self.ui.opt_sens_status_label.isEnabled() and self.check_cnt >= 3:
                        self.ui.opt_sens_status_label.setText("OPT. SENSOR IS DISCONNECTED")
                        self.ui.opt_sens_status_label.setStyleSheet("color: orange;")
                        self.ui.opt_sens_status_label.setEnabled(False)
                        self.check_cnt = 0
                    elif self.check_cnt >= 3:
                        self.ui.opt_sens_status_label.setText("OR TRY LOAD WAVELENGTHS")
                        self.ui.opt_sens_status_label.setStyleSheet("color: orange;")
                        self.ui.opt_sens_status_label.setEnabled(True)
                        self.check_cnt = 0
                else:
                    self.ui.btn_opt_unlocked.setHidden(True)
                    self.ui.opt_sens_status_label.setText("OPT. SENSOR IS DISCONNECTED")
                    self.ui.opt_sens_status_label.setStyleSheet("color: orange;")

            if self.sensor_ref_check != 0:
                if self.sensor_ref_check == 1:
                    self.ui.ref_sens_status_label.setText("REF. SENSOR IS CONNECTED")
                    self.ui.ref_sens_status_label.setStyleSheet("color: blue;")
                elif self.sensor_ref_check == 2:
                    self.ui.ref_sens_status_label.setText("REF. SENSOR IS READY")
                    self.ui.ref_sens_status_label.setStyleSheet("color: green;")
                elif self.sensor_ref_check == 6:
                    self.ui.ref_sens_status_label.setText("REF. SENSOR IS NOT READY")
                    self.ui.ref_sens_status_label.setStyleSheet("color: red;")
                elif self.sensor_ref_check == 3:
                    self.ui.ref_sens_status_label.setText("REF. USB DEVICE DISCONNECTED!")
                    if self.ui.ref_sens_status_label.isEnabled():
                        self.ui.ref_sens_status_label.setStyleSheet("color: red;")
                        self.ui.ref_sens_status_label.setEnabled(False)
                    else:
                        self.ui.ref_sens_status_label.setStyleSheet("color: black;")
                        self.ui.ref_sens_status_label.setEnabled(True)
                elif self.sensor_ref_check == -1:
                    self.ui.ref_sens_status_label.setText("REF. SENSOR INITIALIZATION")
                    self.ui.ref_sens_status_label.setStyleSheet("color: black;")
            else:
                self.ui.ref_sens_status_label.setText("REF. SENSOR IS NOT CONNECTED")
                self.ui.ref_sens_status_label.setStyleSheet("color: orange;")

            if not self.sensor_gen_check:
                self.ui.gen_status_label_2.setHidden(False)
                if self.ui.gen_status_label.isEnabled():
                    self.ui.gen_status_label_2.setText("DISCONNECTED")
                    self.ui.gen_status_label.setStyleSheet("color: red;")
                    self.ui.gen_status_label_2.setStyleSheet("color: red;")
                    self.ui.gen_status_label.setEnabled(False)
                else:
                    self.ui.gen_status_label_2.setText("CONNECTED IT !")
                    self.ui.gen_status_label.setStyleSheet("color: black;")
                    self.ui.gen_status_label_2.setStyleSheet("color: black;")
                    self.ui.gen_status_label.setEnabled(True)
            else:
                if self.sensor_gen_error:
                    self.ui.gen_status_label_2.setHidden(False)
                    if self.ui.gen_status_label.isEnabled():
                        self.ui.gen_status_label_2.setText("DISCONNECTED")
                        self.ui.gen_status_label.setStyleSheet("color: red;")
                        self.ui.gen_status_label_2.setStyleSheet("color: red;")
                        self.ui.gen_status_label.setEnabled(False)
                    else:
                        self.ui.gen_status_label_2.setText("RESTART IT !")
                        self.ui.gen_status_label.setStyleSheet("color: black;")
                        self.ui.gen_status_label_2.setStyleSheet("color: black;")
                        self.ui.gen_status_label.setEnabled(True)
                else:
                    self.ui.gen_status_label.setStyleSheet("color: black;")
                    self.ui.gen_status_label_2.setHidden(True)

    def config_changed(self, text):
        self.window.current_conf = False
        self.my_settings.save_config_file(False, self.window.config_file_path)

        self.config_file = text
        self.config_file_path = os_path.join(self.my_settings.subfolderConfig_path, self.config_file)
        self.window.config_file_path = self.config_file_path
        self.my_settings.load_config_file(self.window.config_file_path)

        self.window.current_conf = True
        self.my_settings.save_config_file(True, self.window.config_file_path)
        self.ui.plot_graph_check.setChecked(self.my_settings.calib_plot)
        kill_sentinel(False, True)
        start_sentinel_modbus(self.my_settings.folder_sentinel_modbus_folder,
                              self.my_settings.folder_sentinel_D_folder,
                              self.my_settings.opt_project,
                              self.my_settings.opt_channels)
        if self.my_settings.opt_channels >= 2:
            self.ui.btn_load_wl.setHidden(False)
        else:
            self.ui.btn_load_wl.setHidden(True)
        self.load_gen_params_labels()

    def set_s_n(self, text=None):
        if text is None:
            text = self.ui.S_N_line.text()

        def format_serial_number(serial, div):
            match = re_search(r"(\d+)(\D+)(\d+)", serial)
            if match:
                part1 = match.group(1)
                part3 = int(match.group(3))  # Convert to integer to remove leading zeros

                formatted_serial = f"{part1}{div}{part3:04}"  # Format the integer with leading zeros to a width of 4
                return formatted_serial
            else:
                return serial

        self.s_n_export = format_serial_number(text, "/")
        self.s_n = format_serial_number(text, "_")
        self.ui.S_N_line.blockSignals(True)
        self.ui.S_N_line.setText(self.s_n)
        self.ui.S_N_line.blockSignals(False)

    def btn_connect_load_wl(self):
        attempt_count = 0
        max_attempts = 10
        self.ui.output_browser_3.setText("Loading wavelengths")
        while attempt_count < max_attempts:
            try:
                order_id = re_search(r'(-?\d+(\.\d+)?)', self.s_n).group(1)
                if self.my_settings.opt_channels not in [0, 1]:
                    kill_sentinel(False, True)
                    result = set_wavelengths(order_id, self.my_settings.folder_sentinel_D_folder,
                                             self.my_settings.opt_project)
                    if result == 0:
                        self.ui.output_browser_3.setText("Could not extract wavelengths from received data")
                    elif result == -1:
                        self.ui.output_browser_3.setText("Error connecting to the database")
                    elif result == -2:
                        self.ui.output_browser_3.setText("Error while setting wavelengths")
                    else:
                        self.ui.output_browser_3.setText("Wavelengths were successfully loaded")
                    start_sentinel_modbus(self.my_settings.folder_sentinel_modbus_folder,
                                          self.my_settings.folder_sentinel_D_folder,
                                          self.my_settings.opt_project, self.my_settings.opt_channels)
                    break
            except Exception as e:
                attempt_count += 1
                if attempt_count >= max_attempts:
                    self.ui.output_browser_3.setText(f"Error occurred while loading SN :\n{e}")
                    break

    def open_settings_window(self):
        self.settings_window = MySettingsWindow(False, self.window, self.my_settings)
        self.hide()
        self.settings_window.show()

    def update_progress_bar(self, value):
        progress_sec = value
        if progress_sec < self.my_settings.ref_measure_time:
            self.ui.progressBar.setValue(int(100 * progress_sec / self.my_settings.ref_measure_time))
        else:
            prog_finish = int(100 * progress_sec / self.my_settings.ref_measure_time)
            if prog_finish < 100:
                self.ui.progressBar.setValue(int(100 * progress_sec / self.my_settings.ref_measure_time))
            else:
                self.ui.progressBar.setValue(100)

    def enable_stop_btn(self):
        self.ui.stop_btn.setEnabled(True)

    def load_gen_params_labels(self):
        self.ui.label_start_freq.setText(str(self.my_settings.generator_sweep_start_freq) + " Hz")
        self.ui.label_stop_freq.setText(str(self.my_settings.generator_sweep_stop_freq) + " Hz")
        self.ui.label_mvpp.setText(str(self.my_settings.generator_max_mvpp) + " mVpp")
        self.ui.label_sweep_type.setText(self.my_settings.generator_sweep_type)
        self.ui.label_sweep_time.setText(str(self.my_settings.generator_sweep_time) + " s")

    def showEvent(self, event):
        if self.my_settings.opt_channels >= 2:
            self.ui.btn_load_wl.setHidden(False)
        else:
            self.ui.btn_load_wl.setHidden(True)
        self.setFixedSize(int(self.width() * self.window.window_scale_delta),
                          int(self.height() * self.window.window_scale_delta))
        scale_app(self, self.window.window_scale_delta)
        self.window.window_scale_delta = 1
        center_on_screen(self)
        self.ui.plot_graph_check.setChecked(self.my_settings.calib_plot)
        load_all_config_files(self.ui.select_config, self.window.config_file_path,
                              self.my_settings.opt_sensor_type,
                              self.my_settings.subfolderConfig_path)
        # label info o opt senz

        self.load_gen_params_labels()

        if self.prev_opt_channel != self.my_settings.opt_channels:
            kill_sentinel(False, True)
            start_sentinel_modbus(self.my_settings.folder_sentinel_modbus_folder,
                                  self.my_settings.folder_sentinel_D_folder,
                                  self.my_settings.opt_project, self.my_settings.opt_channels)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to exit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clean up resources or save any data if needed before exiting
            kill_sentinel(True, True)
            # self.autoCalib.calib_figure.close()
            pyplot_close('all')
            try:
                self.autoCalib.thread_check_sin_opt.termination = True
                self.autoCalib.thread_check_sin_ref.termination = True
            except:
                pass
            win32api.LoadKeyboardLayout(self.native_keyboard_layout, win32con.KLF_ACTIVATE)
            event.accept()
        else:
            event.ignore()


#  meranie + kalibrácia
class AutoCalibMain:
    from ThreadControlFuncGen import ThreadControlFuncGen
    from ThreadRefSensDataCollection import ThreadRefSensDataCollection
    from ThreadProgressBar import ThreadProgressBar
    from ThreadOptAndGenCheckIfReady import ThreadOptAndGenCheckIfReady
    from ThreadSentinelCheckNewFile import ThreadSentinelCheckNewFile
    from ThreadSensorsCheckIfReady import ThreadSensorsCheckIfReady
    from ThreadRefCheckIfReady import ThreadRefCheckIfReady

    def __init__(self, calib_window: MyMainWindow, my_settings: MySettings, thcfgs: ThreadControlFuncGenStatements):
        self.offset = None
        self.last_s_n_export = None
        self.last_s_n = None
        self.export_folder = None
        self.calib_result = True
        self.export_status = True
        self.database = DatabaseCom()
        self.time_stamp = None
        self.calibration_profile = None
        self.calib_output = None
        self.my_settings = my_settings
        self.start_window = calib_window.window
        self.calib_window = calib_window
        self.thcfgs = thcfgs
        # self.calib_figure = self.FiguresWindow(self.calib_window)
        self.acc_calib = None
        # self.refData = None
        self.current_date = None
        self.time_string = None
        self.opt_sentinel_file_name = None
        self.thread_control_gen = self.ThreadControlFuncGen(self.my_settings.generator_id,
                                                            self.my_settings.generator_sweep_time,
                                                            self.my_settings.generator_sweep_start_freq,
                                                            self.my_settings.generator_sweep_stop_freq,
                                                            self.my_settings.generator_sweep_type,
                                                            self.my_settings.generator_max_mvpp,
                                                            self.thcfgs,
                                                            self.my_settings.opt_project,
                                                            self.my_settings.opt_channels,
                                                            self.my_settings.folder_sentinel_D_folder)
        self.thread_check_new_file = self.ThreadSentinelCheckNewFile(self.my_settings.folder_opt_export)
        self.thread_ref_sens = self.ThreadRefSensDataCollection(self.start_window, self.thcfgs,
                                                                self.calib_window.s_n, self.my_settings,
                                                                self.calib_window.s_n_export)
        self.thread_prog_bar = self.ThreadProgressBar(int(self.my_settings.ref_measure_time),
                                                      self.thcfgs)
        self.thread_check_sensors = self.ThreadSensorsCheckIfReady(self.thcfgs)
        self.thread_check_sin_opt = self.ThreadOptAndGenCheckIfReady("127.0.0.1", 501, 1,
                                                                     100, 25, 0.003,
                                                                     self.start_window, self.my_settings, self.thcfgs)
        self.thread_check_sin_ref = self.ThreadRefCheckIfReady(self.thcfgs, self.start_window, self.my_settings)

        self.sensitivities_file = "sensitivities.csv"
        self.time_corrections_file = "time_corrections.csv"

    def ref_check_finished(self):
        # print("END -------> REF CHECK")
        try:
            self.thread_check_sin_ref.task_sin.close()
        except:
            pass
        self.thcfgs.set_end_sens_test(True)
        self.thread_check_new_file.start()
        self.calib_window.ui.ref_value_max_g_label.setText("-")
        self.calib_window.ui.opt_value_wl_label.setText("-")

        from nidaqmx import Task as nidaqmx_Task
        from nidaqmx.constants import AcquisitionType

        self.thread_ref_sens.task = nidaqmx_Task(new_task_name='RefMeasuring')
        self.thread_ref_sens.task.ai_channels.add_ai_accel_chan(
            self.my_settings.ref_device_name + '/' + self.my_settings.ref_channel,
            sensitivity=self.my_settings.calib_reference_sensitivity * 9.80665)
        # časovanie resp. vzorkovacia freqvencia, pocet vzoriek
        self.thread_ref_sens.task.timing.cfg_samp_clk_timing(self.my_settings.ref_sample_rate,
                                                             sample_mode=AcquisitionType.CONTINUOUS)
        # self.thread_ref_sens.task.timing.cfg_samp_clk_timing(self.my_settings.ref_sample_rate,
        #                                                      sample_mode=AcquisitionType.FINITE,
        #                                                      samps_per_chan=int(
        #                                                          self.my_settings.ref_number_of_samples))

    def start(self):
        self.calib_window.ui.S_N_line.clear()
        self.thcfgs.set_finished_measuring(False)
        self.thcfgs.set_start_sens_test(False)
        self.thcfgs.set_end_sens_test(False)
        self.thcfgs.set_start_measuring(False)
        self.calib_window.ui.progressBar.setValue(0)
        self.calib_window.opt_force = False
        self.calib_window.sensor_ref_check = -1
        self.calib_window.sensor_opt_check = -1
        self.thcfgs.set_finished_measuring(False)
        # print("START() CHECKING SENSORS -------------")
        # print("SENS IS RUNNING ? : " + str(self.thread_check_sensors.isRunning()))
        # print("OPT IS RUNNING ? : " + str(self.thread_check_sin_opt.isRunning()))
        # print("REF IS RUNNING ? : " + str(self.thread_check_sin_ref.isRunning()))
        # print("CONTROL GEN IS RUNNING ? : " + str(self.thread_control_gen.isRunning()))
        # print("PROG IS RUNNING ? : " + str(self.thread_prog_bar.isRunning()))
        # print("REF MEASURE GEN IS RUNNING ? : " + str(self.thread_ref_sens.isRunning()))

        self.calib_window.measure = False

        self.thread_check_sin_ref = self.ThreadRefCheckIfReady(self.thcfgs, self.start_window, self.my_settings)
        self.thread_check_sin_ref.check_ready.connect(self.calib_window.ref_emit)
        self.thread_check_sin_ref.finished.connect(self.ref_check_finished)
        self.thread_check_sin_ref.out_value.connect(self.calib_window.update_ref_value)

        self.thread_check_sin_opt = self.ThreadOptAndGenCheckIfReady("127.0.0.1", 501, 1,
                                                                     100, 25, 0.003,
                                                                     self.start_window, self.my_settings, self.thcfgs)
        self.thread_check_sin_opt.check_ready_opt.connect(self.calib_window.opt_emit)
        self.thread_check_sin_opt.check_ready_gen.connect(self.calib_window.gen_emit)
        self.thread_check_sin_opt.check_gen_error.connect(self.calib_window.gen_error_emit)
        self.thread_check_sin_opt.finished.connect(self.opt_finished)
        self.thread_check_sin_opt.out_value.connect(self.calib_window.update_wl_values)
        if self.thread_check_sensors is None:
            print("BUILDING SENS CHECK....")
            self.thread_check_sensors = self.ThreadSensorsCheckIfReady(self.thcfgs, auto_calib=self)
            self.thread_check_sensors.check_ready.connect(self.calib_window.check_sensors_ready)
            # self.thread_check_sensors.finished.connect(self.thread_end_check_sens)
            self.thread_check_sensors.start()
        else:
            if not self.thread_check_sensors.isRunning():
                print("STARTING SENS CHECK....")
                self.thread_check_sensors = self.ThreadSensorsCheckIfReady(self.thcfgs, auto_calib=self)
                self.thread_check_sensors.check_ready.connect(self.calib_window.check_sensors_ready)
                # self.thread_check_sensors.finished.connect(self.thread_end_check_sens)
                self.thread_check_sensors.start()
            else:
                print("SENSORS CHECK IS RUNNING....")

        self.thread_check_sin_ref.start()
        self.thread_check_sin_opt.start()
        self.calib_window.ui.start_btn.setEnabled(False)
        self.calib_window.ui.start_btn.setHidden(False)
        self.calib_window.ui.stop_btn.setHidden(True)
        self.calib_window.ui.stop_btn.setEnabled(True)

        self.calib_window.ui.stop_btn.setEnabled(False)
        self.calib_window.ui.S_N_line.setEnabled(True)
        self.calib_window.ui.btn_settings.setEnabled(True)
        self.calib_window.ui.select_config.setEnabled(True)
        self.calib_window.ui.plot_graph_check.setEnabled(True)
        self.calib_window.ui.menubar.setEnabled(True)

    def opt_finished(self):
        self.calib_window.ui.opt_value_wl_label.setText("-")
        # print("END -------> OPT CHECK")

    # def thread_end_check_sens(self):
    #     self.calib_window.ui.start_btn.setEnabled(False)
    #     print("END ------> CHECK SENS")
    #     self.start()

    def thread_control_gen_finished(self):
        print("END -------> CONTROL GEN")

        if self.thcfgs.get_emergency_stop():
            self.calib_window.ui.start_btn.setEnabled(False)
            self.calib_window.ui.start_btn.setHidden(False)
            self.calib_window.ui.stop_btn.setHidden(True)
            self.calib_window.ui.stop_btn.setEnabled(True)

            if not self.thcfgs.get_start_measuring() and self.thcfgs.get_end_sens_test():
                self.thread_ref_sens.task.close()
                self.start()
            if self.thread_check_new_file is not None and self.thread_check_new_file.isRunning():
                self.thread_check_new_file.termination = True
            self.thcfgs.set_finished_measuring(False)
            self.thcfgs.set_start_sens_test(False)
            self.thcfgs.set_end_sens_test(False)
            self.thcfgs.set_start_measuring(False)
        else:
            self.calib_window.ui.output_browser_3.setText("Calibration ...")

    def terminate_measure_threads(self):
        self.thread_ref_sens.terminate()
        kill_sentinel(True, False)

    def on_btn_start_clicked(self):  # start merania
        self.thcfgs.set_emergency_stop(False)
        attempt_count = 0
        max_attempts = 5
        msg_box = None
        try:
            # self.calib_figure.hide()
            pyplot_close('all')
            start_calibration = True
            print(os_path.exists(
                            os_path.join(self.my_settings.folder_calibration_export,
                                         self.calib_window.s_n + '.csv')))
            print(self.export_status)
            print(self.calib_result)

            while attempt_count < max_attempts:
                try:
                    if not self.export_status and self.calib_result:
                        self.calib_window.setEnabled(False)
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Information)
                        msg_box.setText("You have not exported calibration result, do you want to continue anyway?")
                        msg_box.setWindowTitle("Proceed?")
                        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        export_button = msg_box.addButton("Export", QMessageBox.ActionRole)
                        return_value = msg_box.exec()
                        if return_value == QMessageBox.Yes:
                            start_calibration = True
                        elif msg_box.clickedButton() == export_button:
                            self.calib_window.exp_btn_clicked()
                            start_calibration = True
                        else:
                            start_calibration = False
                        self.calib_window.setEnabled(True)
                    elif os_path.exists(
                            os_path.join(self.my_settings.folder_calibration_export,
                                         self.calib_window.s_n + '.csv')) and self.export_status:
                        self.calib_window.setEnabled(False)
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Information)
                        msg_box.setText("Do you want to re-calibrate this sensor?")
                        msg_box.setWindowTitle("Re-calibrate Sensor?")
                        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        return_value = msg_box.exec()
                        if return_value == QMessageBox.Yes:
                            start_calibration = True
                        else:
                            start_calibration = False
                        self.calib_window.setEnabled(True)

                    break  # Exit the loop if successful
                except Exception as e:
                    attempt_count += 1
                    if msg_box:
                        msg_box.close()
                    if attempt_count >= max_attempts:
                        self.calib_window.ui.output_browser_3.setText(
                            f"Error occurred, (try again or restart app) :\n{e}")
                        return

            if start_calibration:
                self.calib_window.ui.output_browser.clear()
                self.calib_window.ui.output_browser_2.clear()
                self.thcfgs.set_start_measuring(False)
                self.thcfgs.set_start_sens_test(False)
                self.thcfgs.set_end_sens_test(False)
                self.calib_window.ui.pass_status_label.setText("PASS")
                self.calib_window.ui.fail_status_label.setText("FAIL")
                self.calib_window.ui.pass_status_label.setStyleSheet("color: rgba(170, 170, 127,150);")
                self.calib_window.ui.fail_status_label.setStyleSheet("color: rgba(170, 170, 127,150);")
                self.calib_window.ui.export_fail_btn.setEnabled(False)
                self.calib_window.ui.export_pass_btn.setEnabled(False)
                self.calib_window.measure = True
                self.calib_window.ui.S_N_line.setEnabled(False)
                self.calib_window.ui.btn_settings.setEnabled(False)
                self.calib_window.ui.btn_load_wl.setEnabled(False)
                self.calib_window.ui.select_config.setEnabled(False)
                self.calib_window.ui.plot_graph_check.setEnabled(False)
                self.calib_window.ui.menubar.setEnabled(False)
                self.calib_window.ui.start_btn.setEnabled(False)

                self.thread_control_gen = self.ThreadControlFuncGen(self.my_settings.generator_id,
                                                                    self.my_settings.generator_sweep_time,
                                                                    self.my_settings.generator_sweep_start_freq,
                                                                    self.my_settings.generator_sweep_stop_freq,
                                                                    self.my_settings.generator_sweep_type,
                                                                    self.my_settings.generator_max_mvpp,
                                                                    self.thcfgs,
                                                                    self.my_settings.opt_project,
                                                                    self.my_settings.opt_channels,
                                                                    self.my_settings.folder_sentinel_D_folder)

                self.thread_control_gen.connected_status.connect(self.calib_window.gen_emit)
                self.thread_control_gen.step_status.connect(self.calib_window.write_to_output_browser)
                self.thread_control_gen.finished.connect(self.thread_control_gen_finished)
                self.thread_control_gen.set_btn.connect(self.calib_window.enable_stop_btn)

                self.thread_check_new_file = self.ThreadSentinelCheckNewFile(
                    self.my_settings.folder_opt_export)
                self.thread_check_new_file.finished.connect(self.thread_check_new_file_finished)

                self.thread_prog_bar = self.ThreadProgressBar(int(self.my_settings.ref_measure_time),
                                                              self.thcfgs, auto_calib=self)
                # print("FILE NAME:")
                # print(self.opt_sentinel_file_name)
                self.thread_ref_sens = self.ThreadRefSensDataCollection(self.start_window, self.thcfgs,
                                                                        self.calib_window.s_n, self.my_settings,
                                                                        self.calib_window.s_n_export)
                #
                self.thread_prog_bar.finished.connect(self.thread_prog_bar_finished)
                self.thread_prog_bar.progress_signal.connect(self.calib_window.update_progress_bar)
                self.thread_ref_sens.finished.connect(self.thread_ref_sens_finished)
                self.thread_control_gen.start()
                self.calib_window.ui.stop_btn.setHidden(False)
                self.calib_window.ui.start_btn.setHidden(True)
                self.calib_window.ui.start_btn.setEnabled(False)
                self.calibration_profile = f"{self.my_settings.generator_sweep_start_freq}-{self.my_settings.generator_sweep_stop_freq}Hz; {self.my_settings.generator_max_mvpp}mVpp; {self.my_settings.generator_sweep_time}s; {self.my_settings.generator_sweep_type}"
        except Exception as e:
            self.calib_window.ui.output_browser_3.setText(f"Error occurred, (try again) :\n{e}")

    def thread_ref_sens_finished(self):
        print("END -------> REF MEASURE")
        # print("EMERGENCY STOP : " + str(self.thcfgs.get_emergency_stop()))
        if not self.thcfgs.get_emergency_stop():
            acc_calib = self.thread_ref_sens.acc_calib
            sens_diff = np_abs(self.my_settings.calib_optical_sensitivity - acc_calib[1])
            strike = 0

            if sens_diff < self.my_settings.calib_optical_sens_tolerance:
                sens_color = "black"
            elif sens_diff < self.my_settings.calib_optical_sens_tolerance * 1.005:
                sens_color = "orange"
                strike += 1
            else:
                sens_color = "red"
                strike += 2

            if np_abs(acc_calib[7]) < 1.0:
                diff_color = "black"
            elif np_abs(acc_calib[7]) < 2.0:
                diff_color = "orange"
                strike += 1
            else:
                diff_color = "red"
                strike += 2

            fltnss_color = "black"

            # self.calib_window.ui.output_browser_3.setText("Calibration results: ")

            self.calib_window.ui.output_browser_2.setText(f"<font><b>{self.calib_window.s_n_export}</b></font>")
            self.calib_window.ui.output_browser.setText("# SN :")

            if len(acc_calib) <= 9:
                self.calib_window.ui.output_browser.append("# Center wavelength :")
                self.calib_window.ui.output_browser_2.append(str(acc_calib[0]) + ' nm')
            else:
                self.calib_window.ui.output_browser.append("# Center wavelengths :")
                self.calib_window.ui.output_browser_2.append(str(acc_calib[0]) + '; ' + str(acc_calib[9]) +
                                                              ' nm')

            self.calib_window.ui.output_browser.append("# Sensitivity : " + '\n' +
                                                       "# Sensitivity flatness : " + '\n' +
                                                       "# Difference in symmetry : ")

            self.calib_window.ui.output_browser_2.append(
                f"<font color='{sens_color}'>{str(round(acc_calib[1], 3))} pm/g at {str(self.my_settings.calib_gain_mark)} Hz</font>"
            )

            self.calib_window.ui.output_browser_2.append(
                f"<font color='{fltnss_color}'>{str(acc_calib[4])} between {str(acc_calib[2])} Hz and  {str(acc_calib[3])} Hz</font>"
            )

            self.calib_window.ui.output_browser_2.append(
                f"<font color='{diff_color}'>{acc_calib[7]} %</font>"
            )

            self.check_if_calib_is_valid(strike)

            self.calib_window.ui.S_N_line.setEnabled(True)
            self.calib_window.ui.btn_settings.setEnabled(True)
            self.calib_window.ui.select_config.setEnabled(True)
            self.calib_window.ui.plot_graph_check.setEnabled(True)
            self.calib_window.ui.menubar.setEnabled(True)
            self.calib_output = self.thread_ref_sens.out
            self.time_stamp = self.thread_ref_sens.time_stamp
            self.acc_calib = self.thread_ref_sens.acc_calib
            self.last_s_n = self.calib_window.s_n
            self.last_s_n_export = self.calib_window.s_n_export
            if self.my_settings.calib_plot:
                self.plot_graphs(self.calib_output)
                # self.calib_figure.init_ui(self.thread_ref_sens.out)
                # self.calib_figure.show()
        else:
            self.calib_window.ui.output_browser_3.setText("EMERGENCY SHUTDOWN FINISHED")
            start_sentinel_modbus(self.my_settings.folder_sentinel_modbus_folder,
                                  self.my_settings.folder_sentinel_D_folder,
                                  self.my_settings.opt_project, self.my_settings.opt_channels)
        self.start()
        self.export_to_database()

    def plot_graphs(self, out):
        title_font_size = 12
        label_font_size = 16
        plt.figure("Calibration figures")

        # Plot for Resized filtered data
        plt.subplot(2, 1, 1)  # 1 row, 2 columns, first plot
        plt.plot(out[1], out[2], label='Optical')
        plt.plot(out[3], out[4], label='Reference')
        plt.legend()
        plt.title('Resampled and resized data of ' + self.opt_sentinel_file_name, fontsize=title_font_size)
        plt.ylabel('Acceleration [g]', fontsize=label_font_size)
        plt.xlabel('Time[s]', fontsize=label_font_size)
        plt.grid(which='both')
        plt.minorticks_on()

        # Plot for Power spectrum
        if self.my_settings.calib_do_spectrum:
            plt.subplot(2, 1, 2)  # 1 row, 2 columns, second plot
            plt.plot(out[5], out[6], label='Optical')
            plt.plot(out[7], out[8], label='Reference')
            plt.legend()
            plt.title('Spectrum of ' + self.opt_sentinel_file_name, fontsize=title_font_size)
            plt.ylabel('Spectral Density [dB]', fontsize=label_font_size)
            plt.xlabel('Frequency [Hz]', fontsize=label_font_size)
            plt.grid(which='both')
            plt.minorticks_on()
            plt.xlim(self.my_settings.generator_sweep_start_freq,
                     self.my_settings.generator_sweep_stop_freq)

        plt.tight_layout()
        mng = plt.get_current_fig_manager()

        screen = QDesktopWidget().screenGeometry()
        mng.window.resize(int(mng.window.width() + mng.window.width() * 0.1), screen.height())
        fig_width = mng.window.width()
        # Move your parent window (self.window) flush to the right of the Matplotlib window
        current_y = self.calib_window.y()
        self.calib_window.move(fig_width, current_y)
        plt.show(block=False)

    def thread_prog_bar_finished(self):
        print("END ------> PROG BAR")
        self.calib_window.ui.progressBar.setValue(0)

    def thread_check_new_file_finished(self):
        print("END ----------->check_new_file")
        if not self.thcfgs.get_emergency_stop():
            self.thread_ref_sens.start()
            self.opt_sentinel_file_name = self.thread_check_new_file.opt_sentinel_file_name
            self.thread_prog_bar.start()
            self.thcfgs.set_start_measuring(True)
        else:
            print("KILL SENTINEL START MODBUS")
            kill_sentinel(True, True)
            start_sentinel_modbus(self.my_settings.folder_sentinel_modbus_folder,
                                  self.my_settings.folder_sentinel_D_folder, self.my_settings.opt_project,
                                  self.my_settings.opt_channels)

    def check_if_calib_is_valid(self, acc_calib):
        if acc_calib <= 1:
            self.calib_window.ui.pass_status_label.setStyleSheet("color: green;")
            self.calib_window.ui.fail_status_label.setText("NOTE")
            self.calib_window.ui.fail_status_label.setStyleSheet("color: grey;")
            self.calib_window.ui.export_pass_btn.setEnabled(True)
            self.calib_window.ui.export_fail_btn.setEnabled(False)
            self.export_status = False
            self.calib_result = True
        else:
            self.calib_window.ui.fail_status_label.setStyleSheet("color: red;")
            self.calib_window.ui.pass_status_label.setText("EXPORT")
            self.calib_window.ui.pass_status_label.setStyleSheet("color: grey;")
            self.calib_window.ui.export_fail_btn.setEnabled(True)
            self.calib_window.ui.export_pass_btn.setEnabled(False)
            self.export_status = True
            self.calib_result = False

    def export_to_database(self, notes="", btn=False):
        if self.calib_result or btn:
            try:
                params = get_params(self.last_s_n)
                add = [self.last_s_n_export, None, None, True, self.acc_calib[1],   self.acc_calib[0],
                       self.acc_calib[9] if (len(self.acc_calib) >= 10) else None, self.acc_calib[4],
                       self.acc_calib[10] if (len(self.acc_calib) >= 10) else None,
                       self.acc_calib[7], self.export_folder,
                       self.calibration_profile, None, None, notes, self.time_stamp, self.start_window.operator,
                       "PASS" if self.calib_result else "FAIL"]
                params.extend(add)
                if not self.export_status:
                    res = self.database.export_to_database(params=params)
                    #     self.export_to_local_db(str(params[0]))
                else:
                    res = self.database.update_export_note(self.last_s_n_export, notes)
                if res == 0:
                    self.calib_window.ui.output_browser_3.append("Export to the database was successful!")
                    self.export_status = True
                elif res == 1:
                    self.calib_window.ui.output_browser_3.setText("Note was added successfully!\n"
                                                                  "Calibration result :")
                elif res == -1:
                    self.calib_window.ui.output_browser_3.setText("Error connecting to the database!")
                else:
                    self.calib_window.ui.output_browser_3.setText("Unexpected error!")
            except Exception as e:
                self.calib_window.ui.output_browser_3.setText(f"Unexpected error!\n{e}")
                self.calib_window.ui.output_browser.clear()
                self.calib_window.ui.output_browser_2.clear()

    def export_to_local_db(self, idcko):
        source_folders = {'optical': self.my_settings.folder_opt_export,
                          'reference': self.my_settings.folder_ref_export,
                          'calibration': self.my_settings.folder_calibration_export}
        res, text = copy_files(self.last_s_n, idcko, source_folders, self.my_settings.folder_db_export_folder)
        if res == 0:
            self.calib_window.ui.output_browser_3.setText(text)
        elif res == -1:
            self.calib_window.ui.output_browser_3.setText(text)
            self.calib_window.ui.output_browser.clear()
            self.calib_window.ui.output_browser_2.clear()

        file_name_with_extension = os_path.basename(self.start_window.config_file_path)
        file_name = os_path.splitext(file_name_with_extension)[0]
        res = save_statistics_to_csv(self.my_settings.folder_statistics, file_name, self.time_stamp,
                                     self.last_s_n, self.acc_calib[1], self.acc_calib[0], self.acc_calib[9])
        if res != 0:
            self.calib_window.ui.output_browser_3.setText(res)
            self.calib_window.ui.output_browser.clear()
            self.calib_window.ui.output_browser_2.clear()
