import time
from collections import deque

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import win32api
import win32con
from PyQt5.QtGui import QFont, QIcon, QPixmap, QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QDialog, QVBoxLayout, QLabel, \
    QLineEdit, QDialogButtonBox, QComboBox
from PyQt5.QtCore import QEvent, Qt, QTimer
from os import path as os_path

from DatabaseCom import DatabaseCom
from definitions import (scale_app, center_on_screen,
                         load_all_config_files,
                         show_add_dialog, open_folder_in_explorer, start_peaklogger,
                         fetch_wavelengths_peak_logger, kill_peaklogger, PopupWindow, get_params, save_error,
                         copy_files, save_statistics_to_csv)
from matplotlib import pyplot as plt
import ctypes
from ctypes import wintypes, byref as ctypes_byref
from SensStrain.SettingsParams import MySettings
from re import search as re_search
from SensStrain.TMCStatements import TMCStatements
from SensStrain.MySettingsWindow import MySettingsWindow as MySettingsWindowStrain
from numpy import abs as np_abs
from MyStartUpWindow import MyStartUpWindow
from gui.autoCalibrationStrain import Ui_AutoCalibration


class MyMainWindow(QMainWindow):

    def __init__(self, window: MyStartUpWindow, my_settings: MySettings):
        super().__init__()
        self.opt_plot_steps = []
        self.popup = None
        self.range_locked = True
        self.popup_out_of_range = None
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowMaximizeButtonHint)
        self._sensor_opt_value = []
        self.benchtop_check = False
        self.pid = None
        self.data = deque(maxlen=10000)
        self.first_show = True
        self.block_write = False
        self.s_n_export = None
        self.opt_force = False
        self.sensor_gen_error = False
        self.tmcs = TMCStatements()

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

        layout = QVBoxLayout()

        self.figure_lin, self.ax_lin = plt.subplots()
        self.canvas_lin = FigureCanvas(self.figure_lin)
        self.line_lin, = self.ax_lin.plot([], [])
        self.ax_lin.xaxis.set_visible(False)
        self.ax_lin.yaxis.set_visible(False)
        self.ax_lin.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        self.figure_lin.subplots_adjust(left=0, right=1, top=1, bottom=0)

        layout.addWidget(self.canvas_lin)
        self.ui.widget_graph_lin.setLayout(layout)
        self.ui.widget_graph_lin.setHidden(True)

        layout = QVBoxLayout()

        self.figure_step, self.ax_step = plt.subplots()
        self.canvas_step = FigureCanvas(self.figure_step)
        self.line_step, = self.ax_step.plot([], [])
        self.ax_step.xaxis.set_visible(False)
        self.ax_step.yaxis.set_visible(True)
        self.ax_step.spines[['top', 'right', 'bottom', 'left']].set_visible(False)
        self.figure_step.subplots_adjust(left=0, right=1, top=1, bottom=0)

        layout.addWidget(self.canvas_step)
        self.ui.widget_graph_step.setLayout(layout)
        self.ui.widget_graph_step.setHidden(True)

        self.ui.just_box_6.setEnabled(False)
        self.ui.just_box_7.setEnabled(False)

        self.orig_wid_gen_pos_x = self.ui.widget_gen.pos().x()
        self.orig_wid_gen_pos_y = self.ui.widget_gen.pos().y()
        # open_action = QAction("Options", self)
        # open_action.triggered.connect(self.open_settings_window)
        # self.ui.menuSettings.addAction(open_action)
        self.autoCalib = AutoCalibMain(self, self.my_settings, self.tmcs)
        path = os_path.join(self.my_settings.starting_folder, "images/logo.png")
        self.ui.logo_label.setPixmap(QPixmap(path))

        self.ui.S_N_line.editingFinished.connect(self.set_s_n)

        self.ui.start_btn.clicked.connect(self.autoCalib.on_btn_start_clicked)
        self.ui.stop_btn.clicked.connect(self.emergency_stop_clicked)
        self.ui.plot_graph_check.stateChanged.connect(self.plot_check_changed)
        self.ui.select_config.currentTextChanged.connect(self.config_changed)
        self.ui.btn_settings.clicked.connect(self.open_settings_window)
        self.ui.export_pass_btn.clicked.connect(self.exp_btn_clicked)
        self.ui.export_fail_btn.clicked.connect(self.exp_btn_clicked)
        self.ui.export_fail_btn.installEventFilter(self)
        self.ui.export_pass_btn.installEventFilter(self)

        only_float_to = QDoubleValidator(0.0, self.my_settings.stage_max_limit, 10)
        only_int_by = QIntValidator(0, 10000)
        self.ui.move_by_line.setValidator(only_int_by)
        self.ui.move_to_line.setValidator(only_float_to)
        self.ui.move_by_left.clicked.connect(self.move_by_to_left)
        self.ui.move_by_right.clicked.connect(self.move_by_to_right)
        self.ui.move_by_unit.clicked.connect(self.change_move_by_unit)
        self.ui.move_to_start.clicked.connect(self.move_to)
        print(self.ui.move_by_unit.text())

        self.ui.actionmain_folder.triggered.connect(self.open_main_folder)
        self.ui.actioncalibration_folder.triggered.connect(self.open_calib_folder)

        self.ui.actionAdd_new_operator.triggered.connect(self.add_new_operator)
        self.ui.actionChange_operator.triggered.connect(self.change_operator)

        self.ui.actionopen.triggered.connect(self.open_help)

        self.ui.progressBar.setValue(0)
        self.ui.start_btn.setEnabled(False)
        font = QFont("Arial", 10)
        font2 = QFont("Arial", 12)
        self.ui.output_browser_2.setFont(font)
        self.ui.output_browser.setFont(font)
        self.ui.output_browser_3.setFont(font2)
        self.ui.btn_lock_unlock_range.clicked.connect(self.lock_unlock_range)
        self.ui.btn_lock_unlock_range.setStyleSheet("background: transparent; border: none; text-align: center;")
        path = os_path.join(self.my_settings.starting_folder, "images/unlock.png")
        icon = QIcon(QPixmap(path))
        self.ui.btn_lock_unlock_range_placeholder_2.setIcon(icon)
        self.ui.btn_lock_unlock_range_placeholder_2.setIconSize(self.ui.btn_lock_unlock_range_placeholder_2.sizeHint())
        self.ui.btn_lock_unlock_range_placeholder_2.setStyleSheet(
            "background: transparent; border: none; text-align: center;")
        self.ui.btn_lock_unlock_range_placeholder_2.setHidden(True)

        path = os_path.join(self.my_settings.starting_folder, "images/lock.png")
        icon = QIcon(QPixmap(path))
        self.ui.btn_lock_unlock_range_placeholder.setIcon(icon)
        self.ui.btn_lock_unlock_range_placeholder.setIconSize(self.ui.btn_lock_unlock_range_placeholder.sizeHint())
        self.ui.btn_lock_unlock_range_placeholder.setStyleSheet(
            "background: transparent; border: none; text-align: center;")
        self.ui.btn_lock_unlock_range_placeholder.setHidden(False)

        self.ui.label_range_lock.setText(self.window.translations[self.window.lang]["range_locked"])

        path = os_path.join(self.my_settings.starting_folder, "images/stairs.png")
        icon = QIcon(QPixmap(path))
        self.ui.btn_show_steps_graph.setIcon(icon)
        self.ui.btn_show_steps_graph.setIconSize(self.ui.btn_show_steps_graph.sizeHint())
        self.ui.btn_show_steps_graph.setStyleSheet(
            "background: transparent; border: none; text-align: center;")
        self.ui.just_box_steps_graph.setHidden(False)
        self.ui.btn_show_steps_graph.clicked.connect(self.show_stairs_graph)

        path = os_path.join(self.my_settings.starting_folder, "images/linear.png")
        icon = QIcon(QPixmap(path))
        self.ui.btn_show_linear_graph.setIcon(icon)
        self.ui.btn_show_linear_graph.setIconSize(self.ui.btn_show_linear_graph.sizeHint())
        self.ui.btn_show_linear_graph.setStyleSheet(
            "background: transparent; border: none; text-align: center;")
        self.ui.just_box_linear_graph.setHidden(True)
        self.ui.btn_show_linear_graph.clicked.connect(self.show_linear_graph)
        if my_settings is None or my_settings.check_if_none():
            self.ui.output_browser_3.setText(self.window.translations[self.window.lang]["load_error"])
        self.ui.widget_help.setHidden(True)
        self.ui.stop_btn.setHidden(True)
        self.ui.gen_status_label.setHidden(False)
        self.change_sens_type_label()
        path = os_path.join(self.my_settings.starting_folder, "images/logo_icon.png")
        self.setWindowIcon(QIcon(path))
        path = os_path.join(self.my_settings.starting_folder, "images/setting_btn.png")
        icon = QIcon(QPixmap(path))
        self.ui.btn_settings.setIcon(icon)
        self.ui.btn_settings.setIconSize(self.ui.btn_settings.sizeHint())
        self.ui.btn_settings.setStyleSheet("background: transparent; border: none; text-align: center;")

        self.prev_opt_channel = self.my_settings.opt_channels
        # Load the User32.dll
        user32 = ctypes.WinDLL('user32', use_last_error=True)

        # Declare the Windows API methods
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        user32.GetKeyboardLayout.restype = wintypes.HKL
        self.start_width = self.width()
        self.start_height = self.height()

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
            self.ui.output_browser_3.setText(self.window.translations[self.window.lang]["key_board_err"])

        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress and not self.isHidden() and not self.ui.S_N_line.hasFocus()
                and not self.block_write and not self.ui.move_by_line.hasFocus() and not self.ui.move_to_line.hasFocus()):
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

    def show_linear_graph(self):
        self.ui.just_box_steps_graph.setHidden(True)
        self.ui.just_box_linear_graph.setHidden(False)

    def show_stairs_graph(self):
        self.ui.just_box_steps_graph.setHidden(False)
        self.ui.just_box_linear_graph.setHidden(True)

    def lock_unlock_range(self):
        if self.range_locked:
            self.ui.btn_lock_unlock_range_placeholder.setHidden(True)
            self.ui.btn_lock_unlock_range_placeholder_2.setHidden(False)
            self.range_locked = False
            msg = self.window.translations[self.window.lang]["range_unlocked_msg"]
        else:
            self.ui.btn_lock_unlock_range_placeholder_2.setHidden(True)
            self.ui.btn_lock_unlock_range_placeholder.setHidden(False)
            self.range_locked = True
            msg = self.window.translations[self.window.lang]["range_locked_msg"]
        self.popup = PopupWindow(msg, parent=self, h=40)
        self.popup.show_for_a_while()

    def update_data_lin_plot(self):
        # Extending data

        self.line_lin.set_ydata(self.tmcs.opt_wls)
        self.line_lin.set_xdata(self.tmcs.ref_pos)

        self.ax_lin.relim()
        self.ax_lin.autoscale_view()

        self.canvas_lin.draw()

    def update_data_step_plot(self):
        # Extending data

        self.line_step.set_ydata(self.opt_plot_steps)
        self.line_step.set_xdata(range(len(self.opt_plot_steps)))

        self.ax_step.relim()
        self.ax_step.autoscale_view()

        self.canvas_step.draw()

    def open_help(self):
        print("Open help --------------------------------------------")
        if self.ui.widget_help.isHidden():
            self.ui.widget_gen.move(-15, self.ui.widget_gen.pos().y())
            self.ui.widget_help.setHidden(False)
            self.setFixedSize(int(self.width() * 1.434), self.height())
            self.ui.actionopen.setText(self.window.translations[self.window.lang]["actionopen_close"])
        else:
            self.setFixedSize(int(self.start_width * self.window.window_scale), self.height())
            self.ui.widget_help.setHidden(True)
            self.ui.widget_gen.move(int(self.orig_wid_gen_pos_x * self.window.window_scale),
                                    int(self.orig_wid_gen_pos_y * self.window.window_scale))
            self.ui.actionopen.setText(self.window.translations[self.window.lang]["actionopen_open"])

    def open_main_folder(self):
        open_folder_in_explorer(self.my_settings.folder_main)

    def open_calib_folder(self):
        open_folder_in_explorer(self.my_settings.folder_calibration_export)

    def change_operator(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.window.translations[self.window.lang]["choose_op"])

        vbox = QVBoxLayout()

        label = QLabel(self.window.translations[self.window.lang]["sel_op"])
        vbox.addWidget(label)

        combo_box = QComboBox()
        for operator in self.window.operators:
            combo_box.addItem(operator)
        vbox.addWidget(combo_box)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        vbox.addWidget(button_box)

        dialog.setLayout(vbox)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window.operator = combo_box.currentText()
            self.ui.menuOperator.setTitle(f"Operator: {self.window.operator}")

    def add_new_operator(self):
        self.block_write = True
        operator = show_add_dialog(self, self.window.starting_folder, start=False)
        if operator:
            self.window.operators.append(operator)
            self.window.operator = operator
            self.ui.menuOperator.setTitle(f"Operator: {self.window.operator}")
        self.block_write = False

    def exp_btn_clicked(self):
        self.block_write = True
        dialog = QDialog(self)
        dialog.setWindowTitle("Export calibration" if not self.autoCalib.export_status else "Add note")

        dialog_layout = QVBoxLayout()

        label = QLabel(self.window.translations[self.window.lang]["add_note"])
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

    def plot_check_changed(self, state):
        try:
            # self.calib_figure.hide()
            self.autoCalib.plot1.hide()
        except:
            pass
        if state == 2:
            self.my_settings.calib_plot = True
            if self.autoCalib.calib_output:
                self.autoCalib.plot1.show()
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
        self.ui.label_opt_sens_type_label.setText(
            self.my_settings.opt_sensor_type + f" {self.window.translations[self.window.lang]['config']}")

    def emergency_stop_clicked(self):
        print("STOP")
        self.ui.output_browser_3.setText(self.window.translations[self.window.lang]["emergency_stop_engaged"])
        self.tmcs.emergency_stop = True
        self.measure = False
        self.ui.S_N_line.setEnabled(True)
        self.ui.btn_settings.setEnabled(True)
        self.ui.select_config.setEnabled(True)
        self.ui.plot_graph_check.setEnabled(True)
        self.ui.menubar.setEnabled(True)

    def first_start(self, op):
        self.ui.menuOperator.setTitle(f"Operator: {op}")
        start_peaklogger(self.window.starting_folder)
        res, _ = fetch_wavelengths_peak_logger(False, timeout_short=5)
        if res == 200:
            self.autoCalib.first_start()
            self.show_back()
            self.window.hide()

    def change_move_by_unit(self):
        units = ["mm", "um", "nm"]
        current_unit = self.ui.move_by_unit.text()
        index = units.index(current_unit)
        next_index = (index + 1) % len(units)
        self.ui.move_by_unit.setText(units[next_index])

    def move_by(self, side):
        unit_map = {
            "mm": 1,
            "um": 1e-03,
            "nm": 1e-06,
            'pm': 1e-09,
        }

        unit = self.ui.move_by_unit.text()
        unit_value = unit_map.get(unit, 4)
        amount = self.ui.move_by_line.text()

        if amount:  # Check if the string is not empty
            try:
                unit_value_stretch = unit_map.get(self.my_settings.max_stretch_unit, 4)
                max_val_stretch = self.my_settings.max_stretch * unit_value_stretch
                length = float(np_abs(float(amount)))  # Convert amount to float before taking absolute value
                value = self.tmcs.current_position + (length * unit_value * side)
                if ((
                            self.my_settings.optical_sensor_mount_position - max_val_stretch * 0.95) <= value <= self.my_settings.optical_sensor_mount_position) or not self.range_locked and value <= self.my_settings.stage_max_limit:
                    self.tmcs.move_by_length = length * unit_value
                    self.tmcs.move_by_direction = side
                    self.tmcs.move_by_action = True
                else:
                    self.show_out_of_range()
            except ValueError:
                # Handle case where the conversion to float fails
                print("Invalid input for amount. Please enter a numerical value.")
        else:
            print("Amount is empty. Please enter a value.")

    def move_by_to_left(self):
        self.move_by(-1)

    def move_by_to_right(self):
        self.move_by(1)

    def move_to(self):
        value = self.ui.move_to_line.text()
        if value:
            unit_map = {
                "mm": 1,
                "um": 1e-03,
                "nm": 1e-06,
                'pm': 1e-09,
            }
            unit_value = unit_map.get(self.my_settings.max_stretch_unit, 4)
            value = float(value)
            max_val_stretch = self.my_settings.max_stretch * unit_value
            if ((
                        self.my_settings.optical_sensor_mount_position - max_val_stretch * 0.95) <= value <= self.my_settings.optical_sensor_mount_position) or not self.range_locked and value <= self.my_settings.stage_max_limit:
                self.tmcs.move_to_position = value
                self.tmcs.move_to_action = True
            else:
                self.show_out_of_range()

    def show_out_of_range(self):
        self.popup_out_of_range = PopupWindow(self.window.translations[self.window.lang]['motor_pos_out_of_range'],
                                              parent=self)
        self.popup_out_of_range.show_for_a_while()

    def opt_emit(self, is_ready, value):
        self.sensor_opt_check = is_ready
        self._sensor_opt_value = value
        if self.tmcs.start:
            self.opt_plot_steps.append(value)
        self.update_wl_values(self._sensor_opt_value)

    def benchtop_emit(self, is_ready):
        self.benchtop_check = is_ready

    def update_wl_values(self, value):
        if value[0] == -1:
            print(0)
            self.ui.opt_value_wl_label.setText("0")
        else:
            wls = ""
            for wl in value:
                print(wl)
                wls += (str(round(wl, 4)) + '\n')

            self.ui.opt_value_wl_label.setText(wls)

    def update_ref_value(self, text):
        if not self.tmcs.init_home:
            text = round(text, 12)
            whole, decimal = str(text).split(".")
            if len(decimal) > 8:
                text = f"{whole}.\n{decimal}"
            else:
                text = f"{whole}.{decimal}\n "
            self.ui.ref_value_max_g_label.setText(str(text))
        else:
            self.ui.ref_value_max_g_label.setText("HOMING")

    def check_sensors_ready(self, check):
        if self.ui.S_N_line.text().strip() and not self.tmcs.init_home:
            if self.sensor_opt_check and self.benchtop_check and not self.measure:
                self.ui.start_btn.setEnabled(True)
            else:
                self.ui.start_btn.setEnabled(True)  # False
        else:
            self.ui.start_btn.setEnabled(True)  # False

        if check:
            if self.tmcs.error:
                if self.ui.ref_sens_status_label.isEnabled():
                    self.ui.ref_sens_status_label.setText(
                        self.window.translations[self.window.lang]["ref_benchtop_status_label"]["error"])
                    self.ui.ref_sens_status_label.setStyleSheet("color: red;")
                    self.ui.ref_sens_status_label.setEnabled(False)
                else:
                    self.ui.ref_sens_status_label.setText(
                        self.window.translations[self.window.lang]["ref_benchtop_status_label"]["error2"])
                    self.ui.ref_sens_status_label.setStyleSheet("color: red;")
                    self.ui.ref_sens_status_label.setEnabled(True)
            elif not self.tmcs.init_home:
                if self.benchtop_check:
                    self.ui.ref_sens_status_label.setText(
                        self.window.translations[self.window.lang]["ref_benchtop_status_label"]["connected"])
                    self.ui.ref_sens_status_label.setStyleSheet("color: blue;")
                else:
                    self.ui.ref_sens_status_label.setText(
                        self.window.translations[self.window.lang]["ref_benchtop_status_label"]["usb_disconnected"])
                    if self.ui.ref_sens_status_label.isEnabled():
                        self.ui.ref_sens_status_label.setStyleSheet("color: red;")
                        self.ui.ref_sens_status_label.setEnabled(False)
                    else:
                        self.ui.ref_sens_status_label.setStyleSheet("color: black;")
                        self.ui.ref_sens_status_label.setEnabled(True)
            else:
                self.ui.ref_sens_status_label.setText(
                    self.window.translations[self.window.lang]["ref_benchtop_status_label"]["calibration"])
                self.ui.ref_sens_status_label.setStyleSheet("color: black;")

            if self.sensor_opt_check:
                if self._sensor_opt_value[0] == -1:
                    self.ui.opt_sens_status_label.setText(
                        self.window.translations[self.window.lang]["opt_sens_status_label"]["not_connected"])
                    self.ui.opt_sens_status_label.setStyleSheet("color: orange;")
                else:
                    self.ui.opt_sens_status_label.setText(
                        self.window.translations[self.window.lang]["opt_sens_status_label"]["connected"])
                    self.ui.opt_sens_status_label.setStyleSheet("color: blue;")
            else:
                self.ui.opt_sens_status_label.setText(
                    self.window.translations[self.window.lang]["opt_sens_status_label"]["peak_logger_disconnected"])
                if self.ui.opt_sens_status_label.isEnabled():
                    self.ui.opt_sens_status_label.setStyleSheet("color: red;")
                    self.ui.opt_sens_status_label.setEnabled(False)
                else:
                    self.ui.opt_sens_status_label.setStyleSheet("color: black;")
                    self.ui.opt_sens_status_label.setEnabled(True)

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

    def open_settings_window(self):
        self.settings_window = MySettingsWindowStrain(False, self.window, self.my_settings)
        self.hide()
        self.settings_window.show_back()

    def update_progress_bar(self, value):
        self.update_data_lin_plot()
        progress_sec = value
        len_val = len(self.tmcs.pos)
        if progress_sec < len_val:
            self.ui.progressBar.setValue(int(100 * progress_sec / len_val))
        else:
            prog_finish = int(100 * progress_sec / len_val)
            if prog_finish < 100:
                self.ui.progressBar.setValue(int(100 * progress_sec / len_val))
            else:
                self.ui.progressBar.setValue(100)

    def enable_stop_btn(self):
        self.ui.stop_btn.setEnabled(True)

    def show_back(self):
        self.set_language()
        self.ui.plot_graph_check.setChecked(self.my_settings.calib_plot)
        load_all_config_files(self.ui.select_config, self.window.config_file_path,
                              self.my_settings.opt_sensor_type,
                              self.my_settings.subfolderConfig_path)
        # label info o opt senz

        if self.first_show:
            self.window.window_scale_delta = self.window.window_scale
            self.first_show = False
        self.setFixedSize(int(self.width() * self.window.window_scale_delta),
                          int(self.height() * self.window.window_scale_delta))
        scale_app(self, self.window.window_scale_delta)

        def bad_scales():
            font = self.ui.plot_graph_check.font()
            font.setPointSize(int(9 * self.window.window_scale))
            self.ui.plot_graph_check.setFont(font)

        QTimer.singleShot(0, lambda: bad_scales())
        self.window.window_scale_delta = 1
        QTimer.singleShot(0, lambda: center_on_screen(self))

    def enable_disable_gui_elements(self, en: bool):
        self.ui.start_btn.setEnabled(False if en else True)
        self.ui.start_btn.setHidden(False if en else True)
        self.ui.stop_btn.setHidden(True if en else False)
        self.ui.stop_btn.setEnabled(True if en else False)

        self.ui.stop_btn.setEnabled(False if en else True)
        self.ui.S_N_line.setEnabled(True if en else False)
        self.ui.btn_settings.setEnabled(True if en else False)
        self.ui.select_config.setEnabled(True if en else False)
        self.ui.plot_graph_check.setEnabled(True if en else False)
        self.ui.menubar.setEnabled(True if en else False)

    def closeEvent(self, event):
        trans = self.window.translations
        lang = self.window.lang
        box = QMessageBox(self)
        # box.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        # Remove only the close button
        box.setWindowFlags(box.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowMinMaxButtonsHint)
        # box.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        box.setWindowTitle(trans[lang]['close_event_a'])
        box.setText(trans[lang]['close_event_b'])

        yes_button = box.addButton(trans[lang]['close_event_yes'], QMessageBox.YesRole)
        no_button = box.addButton(trans[lang]['close_event_no'], QMessageBox.NoRole)

        box.exec_()

        if box.clickedButton() == yes_button:
            self.hide()
            self.tmcs.termination_pos = True
            self.setEnabled(False)
            # Clean up resources or save any data if needed before exiting
            self.tmcs.init_exit = True
            while self.tmcs.init_exit and not self.tmcs.error:
                time.sleep(0.1)
            self.autoCalib.thread_check.termination = True
            self.tmcs.termination = True
            kill_peaklogger()
            win32api.LoadKeyboardLayout(self.native_keyboard_layout, win32con.KLF_ACTIVATE)
            time.sleep(1)
            event.accept()
        else:
            event.ignore()

    def set_language(self):
        trans = self.window.translations
        lang = self.window.lang
        self.ui.ref_sens_status_label.setText(trans[lang]["ref_sens_status_label"]["init"])
        self.ui.opt_sens_status_label.setText(trans[lang]["opt_sens_status_label"]["init"])
        self.ui.label_name_move_to.setText(trans[lang]["label_name_move_to"])
        self.ui.label_name_move_by.setText(trans[lang]["label_name_move_by"])
        self.ui.start_btn.setText(trans[lang]["start_btn"])
        self.ui.plot_graph_check.setText(trans[lang]["plot_graph_check"])
        self.ui.actionAdd_new_operator.setText(trans[lang]["actionAdd_new_operator"])
        self.ui.actionChange_operator.setText(trans[lang]["actionChange_operator"])
        self.ui.label_opt_sens_type_label.setText(
            self.my_settings.opt_sensor_type + f" {self.window.translations[self.window.lang]['config']}")
        if self.ui.widget_help.isHidden():
            self.ui.actionopen.setText(trans[lang]["actionopen_open"])
        else:
            self.ui.actionopen.setText(trans[lang]["actionopen_close"])
        self.ui.menuHelp.setTitle(trans[lang]["menuHelp"])
        self.ui.menuAbout.setTitle(trans[lang]["menuAbout"])

        self.ui.actioncalibration_folder.setText(trans[lang]["actioncalibration_folder"])
        self.ui.actionmain_folder.setText(trans[lang]["actionmain_folder"])
        self.ui.menuOpen_export_folder.setTitle(trans[lang]["menuOpen_export_folder"])

        self.ui.actionwith_project.setText(trans[lang]["actionwith_project"])
        self.ui.actionwithout_project.setText(trans[lang]["actionwithout_project"])

        self.ui.menuoptical_folder_2.setTitle(trans[lang]["menuoptical_folder_2"])
        self.ui.actionraw_opt.setText(trans[lang]["actionraw_opt"])
        self.ui.actionwith_header_opt.setText(trans[lang]["actionwith_header_opt"])

        self.ui.menureference_folder.setTitle(trans[lang]["menureference_folder"])
        self.ui.actionraw_ref.setText(trans[lang]["actionraw_ref"])
        self.ui.actionwith_header_ref.setText(trans[lang]["actionwith_header_ref"])

        self.ui.S_N_line.setPlaceholderText(trans[lang]["S_N_line_placeholder"])

        self.ui.help_text_browser.setText(f"<font><b>{trans[lang]['help_browser']['0']}</b></font>"
                                          f"<font><b>1.</b></font>{trans[lang]['help_browser']['1']}"
                                          f"<font><b>2.</b></font>{trans[lang]['help_browser']['2']}"
                                          f"<font><b>3.</b></font>{trans[lang]['help_browser']['3']}"
                                          f"<font><b>4.</b></font>{trans[lang]['help_browser']['4']}"
                                          f"<font><b>5.</b></font>{trans[lang]['help_browser']['5']}"
                                          f"<font><b>6.</b></font>{trans[lang]['help_browser']['6']}"
                                          f"<font><b>7.</b></font>{trans[lang]['help_browser']['7']}"
                                          f"<font><b>{trans[lang]['help_browser']['a']}</b></font>"
                                          f"<span style='color:green; font-style:italic;'>PASS</span>"
                                          f"{trans[lang]['help_browser']['b']}"
                                          f"<span style='color:red; font-style:italic;'>FAIL</span>"
                                          f"{trans[lang]['help_browser']['c']}"
                                          )

        self.ui.label_range_lock.setText(self.window.translations[self.window.lang]["range_locked"])

    @property
    def sensor_opt_value(self):
        return self._sensor_opt_value

    @sensor_opt_value.setter
    def sensor_opt_value(self, value):
        # You can add any validation or type checks here if needed
        self._sensor_opt_value = value


#  meranie + kalibrácia
class AutoCalibMain:
    from SensStrain.ThreadMotorControl import ThreadMotorControl
    from SensStrain.ThreadMeasure import OptMeasure
    from SensStrain.ThreadCheck import ThreadCheck

    def __init__(self, calib_window: MyMainWindow, my_settings: MySettings, tmcs: TMCStatements):
        self.plot1 = None
        self.wl_slopes = None
        self.offset = None
        self.last_s_n_export = None
        self.last_s_n = None
        self.export_folder = None
        self.calib_result = True
        self.export_status = True
        self.my_settings = my_settings
        self.database = DatabaseCom(self.my_settings.starting_folder)
        self.tmcs = tmcs
        self.time_stamp = None
        self.calibration_profile = None
        self.calib_output = None
        self.calib_window = calib_window
        self.start_window = calib_window.window
        self.strain_calib = None
        self.current_date = None
        self.time_string = None
        self.opt_sentinel_file_name = None
        self.calibration_result = None

        self.thread_motor_control = self.ThreadMotorControl(my_settings, tmcs)
        self.thread_motor_control.update_position.connect(self.calib_window.update_ref_value)
        self.thread_motor_control.start()
        self.tmcs.init_home = True
        self.thread_calibration = self.OptMeasure(self.my_settings, self.tmcs, self.calib_window)

        self.thread_check = self.ThreadCheck(self.start_window, self.tmcs)
        self.thread_check.benchtop_check.connect(self.calib_window.benchtop_emit)
        self.thread_check.opt_check.connect(self.calib_window.opt_emit)
        self.thread_check.update_check.connect(self.calib_window.check_sensors_ready)

    def first_start(self):
        self.thread_check.start()
        self.start()

    def start(self):
        self.calib_window.opt_plot_steps.clear()
        self.calib_window.ui.S_N_line.clear()
        self.calib_window.ui.progressBar.setValue(0)
        self.calib_window.opt_force = False

        # NIECO
        self.calib_window.enable_disable_gui_elements(True)
        self.thread_calibration = self.OptMeasure(self.my_settings, self.tmcs, self.calib_window)
        self.thread_calibration.update.connect(self.calib_window.update_progress_bar)
        self.thread_calibration.finished.connect(self.calibration_finished)
        self.calib_window.ui.progressBar.setValue(50)

    def on_btn_start_clicked(self):  # start merania
        # self.plot1.hide()
        # self.tmcs.emergency_stop = False
        # self.calib_window.enable_disable_gui_elements(False)
        # self.thread_calibration.start()
        self.tmcs.disable_usb_check = True if not self.tmcs.disable_usb_check else False
        self.calib_window.ui.progressBar.setValue(0)
        self.test()

    def test(self):
        value = self.calib_window.ui.progressBar.value() + 1
        self.calib_window.ui.progressBar.setValue(value)
        if self.calib_window.ui.progressBar.value() < 100:
            QTimer.singleShot(100, lambda: self.test())

    def calibration_finished(self):
        self.start()
        self.calibration_result = self.thread_calibration.calibration_results

    def check_if_calib_is_valid(self, strain_calib):
        if strain_calib <= 1:
            self.calib_window.ui.pass_status_label.setStyleSheet("color: green;")
            if self.my_settings.auto_export:
                self.calib_window.ui.fail_status_label.setText("NOTE")
            else:
                self.calib_window.ui.fail_status_label.setText("EXPORT")
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
            self.export_status = False
            self.calib_result = False

    def export_to_database(self, notes="", btn=False):
        if self.calib_result or btn:
            params, params2 = get_params(self.last_s_n, self.my_settings.starting_folder)
            if not self.export_status:
                self.calib_window.ui.output_browser_3.clear()
                if self.my_settings.export_local_server:
                    export_folder = self.export_to_local_db(str(params[0]))
                else:
                    self.calib_window.ui.output_browser_3.setText(f"{self.start_window.translations[self.start_window.lang]['export_to_local_server']}")
                    export_folder = "EXPORT VYPNUTÝ/OFF"
                add = [self.last_s_n_export, None, None, True, self.calibration_result[0], self.calibration_result[1],
                       self.calibration_result[2], self.calibration_result[3], self.calibration_result[4],
                       export_folder,
                       self.calibration_profile, self.calibration_result[5], self.calibration_result[6],
                       self.calibration_result[7], notes, self.time_stamp, self.start_window.operator]
                params.extend(add)
                params.extend(params2)
                params.append("PASS" if self.calib_result else "FAIL")
                res, e = self.database.export_to_database_acc_strain(params=params, sensor="STRAIN")
            else:
                res, e = self.database.update_export_note(self.last_s_n_export, notes, sensor="STRAIN")
            if res == 0:
                self.calib_window.ui.output_browser_3.append(f"{self.start_window.translations[self.start_window.lang]['out_export']}\n")
                self.export_status = True
            elif res == 1:
                self.calib_window.ui.output_browser_3.setText(f"{self.start_window.translations[self.start_window.lang]['out_note_succ']}\n")
            elif res == -1:
                save_error(self.my_settings.starting_folder, e)
                self.calib_window.ui.output_browser_3.setText(self.start_window.translations[self.start_window.lang]['load_wl_error_2'])
            else:
                save_error(self.my_settings.starting_folder, e)
                self.calib_window.ui.output_browser_3.setText("Unexpected error!")

    def export_to_local_db(self, idcko):
        source_folders = {'calibration': self.my_settings.folder_calibration_export}
        if os_path.exists(self.my_settings.folder_db_export_folder):
            res, text, export_folder = copy_files(self.last_s_n, idcko, source_folders, self.my_settings.folder_db_export_folder)
            if res == 0:
                self.calib_window.ui.output_browser_3.setText(self.start_window.translations[self.start_window.lang]["export_to_local_server_success"])
            elif res == -1:
                export_folder = "Súbor so zakázkou nenájdený/Folder with order not found"
                save_error(self.my_settings.starting_folder, text)
                self.calib_window.ui.output_browser_3.setText(text)
                self.calib_window.ui.output_browser.clear()
                self.calib_window.ui.output_browser_2.clear()
        else:
            self.calib_window.ui.output_browser_3.setText(self.start_window.translations[self.start_window.lang]["db_file_path_not_found"])
            export_folder = "Cielova cesta nenájdena/Path not found"
        if os_path.exists(self.my_settings.folder_statistics):
            file_name_with_extension = os_path.basename(self.start_window.config_file_path)
            file_name = os_path.splitext(file_name_with_extension)[0]
            # if self.my_settings.opt_channels >= 2:
            res = save_statistics_to_csv(self.my_settings.folder_statistics, file_name, self.time_stamp,
                                         self.last_s_n_export, self.calibration_result[2], self.calibration_result[0],
                                         self.calibration_result[1])
            # else:
            #     res = save_statistics_to_csv(self.my_settings.folder_statistics, file_name, self.time_stamp,
            #                                  self.last_s_n_export, self.acc_calib[1], self.acc_calib[0])
            if res != 0:
                save_error(self.my_settings.starting_folder, res)
                self.calib_window.ui.output_browser_3.setText(res)
                self.calib_window.ui.output_browser.clear()
                self.calib_window.ui.output_browser_2.clear()
        else:
            self.calib_window.ui.output_browser_3.append(self.start_window.translations[self.start_window.lang]["statistics_file_path_not_found"])
        return export_folder

