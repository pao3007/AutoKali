import time

from PyQt5.QtCore import QTimer, QDate
from PyQt5.QtGui import QPixmap
from codecs import open as codecs_open
from configparser import ConfigParser
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QSplashScreen
from yaml import safe_load as yaml_safe_load, safe_dump as yaml_safe_dump
from os import path as os_path, getcwd as os_getcwd
from gui.start_up import Ui_Setup
from definitions import scale_app, center_on_screen, load_all_config_files, show_add_dialog, start_sentinel_d, \
    save_error, kill_sentinel
from SensAcc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from SensAcc.SettingsParams import MySettings
from json import load as json_load


class MyStartUpWindow(QMainWindow):

    def __init__(self, splash: QSplashScreen):
        super().__init__()
        self.worker = None
        self.bad_ref = False
        self.check_status = False
        self.gen_error = False
        self.gen_connected = False
        self.opt_connected = False
        self.lang = "sk"
        self.version = None
        self.last_ref_calib = None
        self.translations = None
        self.calib_treshold = 180
        self.operators = []
        self.thread_check_usb_devices = None
        self.splash = splash
        self.thcfgs = ThreadControlFuncGenStatements()
        self.window_scale_delta = 1
        self.window_scale = 1
        self.yaml_devices_vendor = 'devices_vendor_ids.yaml'
        self.yaml_database_com = 'database_com.yaml'
        
        self.opt_dev_vendor = None
        self.ref_dev_vendor = None
        self.opt_first_start = True
        self.check_usbs_first_start = True
        self.calib_window = None
        self.settings_window = None
        self.S_N = None
        self.operator = None
        self.current_conf = None
        self.ref_connected = False

        self.starting_folder = os_getcwd()
        self.my_settings = MySettings(self.starting_folder)
        self.my_settings.create_folders()
        self.load_global_settings()

        self.config = None
        self.config_contains_none = True

        self.ui = Ui_Setup()
        self.ui.setupUi(self)
        self.set_language()
        # connect btn
        self.ui.open_settings_btn.clicked.connect(self.open_settings_window)
        self.ui.start_app.clicked.connect(self.start_calib_app)
        self.ui.btn_add_operator.clicked.connect(self.add_remove_operator)
        # connect comboBox
        self.ui.sens_type_comboBox.currentTextChanged.connect(self.sens_type_combobox_changed)
        self.ui.opt_config_combobox.currentTextChanged.connect(self.config_combobox_changed)
        self.ui.combobox_sel_operator.currentIndexChanged.connect(self.operator_changed)

        self.ui.null_detect_label.setHidden(True)
        self.load_operators()

        # buttons
        self.ui.start_app.setEnabled(False)

        # labels
        self.ui.status_opt_label.setStyleSheet("color: black;")
        self.ui.status_ref_label.setStyleSheet("color: black;")
        self.ui.status_gen_label.setStyleSheet("color: black;")
        self.ui.open_settings_btn.setStyleSheet("color: black;")

        #  graphics
        self.ui.logo_label.setPixmap(QPixmap("images/logo.png"))

        self.config_file_path = self.check_config_if_selected()
        self.setup_config()
        self.load_usb_dev_vendors()

        icon = QIcon(QPixmap("images/setting_btn.png"))
        self.ui.open_settings_btn.setIcon(icon)
        self.ui.open_settings_btn.setIconSize(self.ui.open_settings_btn.sizeHint())
        self.ui.open_settings_btn.setStyleSheet("text-align: center;")

        self.setWindowIcon(QIcon('images/logo_icon.png'))
        self.setWindowTitle("Appka")
        self.setFixedSize(self.width(), int(self.height()*0.95))
        scale_app(self, self.window_scale)
        self.setFixedSize(int(self.width() * self.window_scale),
                          int(self.height() * self.window_scale))
        kill_sentinel(True, True)
        self.show_back()

    def add_remove_operator(self):
        def show_remove_dialog():
            def load_and_delete_operator(operator_to_delete, yaml_file_path="operators.yaml"):
                try:
                    # Load YAML file
                    with open(yaml_file_path, 'r') as f:
                        operators = yaml_safe_load(f)

                    # Check if operator exists and delete
                    if operator_to_delete in operators['operators']:
                        operators['operators'].remove(operator_to_delete)

                        # Update YAML file
                        with open(yaml_file_path, 'w') as f:
                            yaml_safe_dump(operators, f)
                        return f"Operator '{operator_to_delete}' successfully deleted."
                    else:
                        return f"Operator '{operator_to_delete}' not found."
                except Exception as e:
                    save_error(self.my_settings.starting_folder, e)
                    return f"An error occurred: {e}"
            op_to_remv = self.ui.combobox_sel_operator.currentText()
            box = QMessageBox(self)
            box.setWindowTitle("Operator")
            box.setText(f"{self.translations[self.lang]['remove_op_msg']}\n{op_to_remv}")

            yes_button = box.addButton(self.translations[self.lang]['close_event_yes'], QMessageBox.YesRole)
            no_button = box.addButton(self.translations[self.lang]['close_event_no'], QMessageBox.NoRole)

            box.exec_()

            if box.clickedButton() == yes_button:
                load_and_delete_operator(op_to_remv)
                self.load_operators()
                self.operator_changed(0)
                # Logic to remove operator here

        if self.ui.combobox_sel_operator.currentIndex() != 0:
            show_remove_dialog()
        else:
            show_add_dialog(self, self.starting_folder)

    def load_operators(self, select_operator=None):
        self.ui.combobox_sel_operator.blockSignals(True)
        self.ui.combobox_sel_operator.clear()
        self.ui.combobox_sel_operator.addItem(self.translations[self.lang]["combobox_sel_operator"])
        file_path = "operators.yaml"
        try:
            with open(file_path, 'r') as f:
                data = yaml_safe_load(f)
            self.operators = data.get('operators', [])
            for operator in self.operators:
                self.ui.combobox_sel_operator.addItem(operator)
            if select_operator:
                self.ui.combobox_sel_operator.setCurrentText(select_operator)
                self.operator_changed(1)
        except Exception as e:
            print(f"An error occurred while loading the YAML file: {e}")
        self.ui.combobox_sel_operator.blockSignals(False)

    def operator_changed(self, idx):
        if idx != 0:
            self.ui.btn_add_operator.setText("-")
        else:
            self.ui.btn_add_operator.setText("+")
        if (self.ref_connected and self.opt_connected and self.gen_connected and self.ui.start_app.text() ==
            self.translations[self.lang]["start_app_a"] and not self.gen_error and
            self.ui.combobox_sel_operator.currentIndex() != 0 and self.my_settings.opt_channels != 0 and not self.config_contains_none and not self.bad_ref):
            self.ui.start_app.setEnabled(True)
        else:
            self.ui.start_app.setEnabled(False)

    def config_combobox_changed(self, text):
        try:
            with open(self.config_file_path, 'r') as file:
                config = yaml_safe_load(file)
            config_file_path = os_path.join(self.my_settings.subfolderConfig_path, text)
            with open(config_file_path, 'r') as file:
                config_check = yaml_safe_load(file)
            if config['opt_measurement']['sensor_type'] == config_check['opt_measurement']['sensor_type']:
                self.current_conf = False
                self.config_contains_none = self.my_settings.save_config_file(False, self.config_file_path)

            self.config_file_path = os_path.join(self.my_settings.subfolderConfig_path, text)
            self.setup_config()
            self.current_conf = True
            self.config_contains_none = self.my_settings.save_config_file(True, self.config_file_path)
        except Exception as e:
            print(e)

    def load_usb_dev_vendors(self):
        config_file_path = os_path.join(self.starting_folder, self.yaml_devices_vendor)
        with open(config_file_path, 'r') as file:
            data = yaml_safe_load(file)

        self.opt_dev_vendor = data['optical']
        self.ref_dev_vendor = data['reference']

    def channel_type_changed(self, index):
        self.my_settings.opt_channels = int(index)

    # def all_dev_connected_signal(self, opt_connected=False, ref_connected=False, gen_connected=False, gen_error=False, check_status=False, bad_ref=False, combobox=False):
    #     if combobox and self.opt_connected is not None:
    #         opt_connected = self.opt_connected
    #         ref_connected = self.ref_connected
    #         gen_connected = self.gen_connected
    #         gen_error = self.gen_error
    #         check_status = self.check_status
    #         bad_ref = self.bad_ref
    #     else:
    #         self.opt_connected = opt_connected
    #         self.ref_connected = ref_connected
    #         self.gen_connected = gen_connected
    #         self.gen_error = gen_error
    #         self.check_status = check_status
    #         self.bad_ref = bad_ref
    #     ow = False
    #     if (ref_connected and opt_connected and gen_connected and self.ui.start_app.text() == self.translations[self.lang]["start_app_a"] and not gen_error and
    #             self.ui.combobox_sel_operator.currentIndex() != 0 and self.my_settings.opt_channels != 0 and not self.config_contains_none and not bad_ref) or ow:
    #         self.ui.start_app.setEnabled(True)
    #     else:
    #         self.ui.start_app.setEnabled(False)
    #
    #     if check_status:
    #         if not self.config_contains_none:
    #             self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
    #             self.ui.open_settings_btn.setStyleSheet("color: black;")
    #         if self.config_contains_none and not ow:
    #             if self.ui.null_detect_label.isEnabled():
    #
    #                 self.ui.null_detect_label.setEnabled(False)
    #
    #                 self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
    #                 self.ui.open_settings_btn.setStyleSheet("color: red;")
    #             else:
    #
    #                 self.ui.null_detect_label.setEnabled(True)
    #
    #                 self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn_err"])
    #                 self.ui.open_settings_btn.setStyleSheet("color: red;")
    #             self.ui.start_app.setEnabled(False)
    #
    #         if not ref_connected and not bad_ref:
    #             self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["disconnect"])
    #             if self.ui.status_ref_label.isEnabled():
    #                 self.ui.status_ref_label.setEnabled(False)
    #                 self.ui.status_ref_label.setStyleSheet("color: black;")
    #             else:
    #                 self.ui.status_ref_label.setEnabled(True)
    #                 self.ui.status_ref_label.setStyleSheet("color: red;")
    #             if self.ref_connected:
    #                 self.check_devices_load_comboboxes()
    #                 self.ref_connected = False
    #         elif bad_ref:
    #             self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["wrong_name"])
    #             if self.ui.status_ref_label.isEnabled():
    #                 self.ui.status_ref_label.setEnabled(False)
    #                 self.ui.status_ref_label.setStyleSheet("color: black;")
    #             else:
    #                 self.ui.status_ref_label.setEnabled(True)
    #                 self.ui.status_ref_label.setStyleSheet("color: red;")
    #             if self.ref_connected:
    #                 self.check_devices_load_comboboxes()
    #                 self.ref_connected = False
    #         else:
    #             self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["connected"])
    #             self.ui.status_ref_label.setStyleSheet("color: green;")
    #             if not self.ref_connected:
    #                 self.ref_connected = True
    #                 self.check_devices_load_comboboxes()
    #
    #         if not opt_connected:
    #             self.ui.status_opt_label.setText(self.translations[self.lang]["status_opt_label"]["disconnect"])
    #             if self.ui.status_opt_label.isEnabled():
    #                 self.ui.status_opt_label.setEnabled(False)
    #                 self.ui.status_opt_label.setStyleSheet("color: black;")
    #             else:
    #                 self.ui.status_opt_label.setEnabled(True)
    #                 self.ui.status_opt_label.setStyleSheet("color: red;")
    #         else:
    #             self.ui.status_opt_label.setText(self.translations[self.lang]["status_opt_label"]["connected"])
    #             self.ui.status_opt_label.setStyleSheet("color: green;")
    #
    #         if not gen_connected:
    #             self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["disconnect"])
    #             if self.ui.status_gen_label.isEnabled():
    #                 self.ui.status_gen_label.setEnabled(False)
    #                 self.ui.status_gen_label.setStyleSheet("color: black;")
    #             else:
    #                 self.ui.status_gen_label.setEnabled(True)
    #                 self.ui.status_gen_label.setStyleSheet("color: red;")
    #         else:
    #             if gen_error:
    #                 if self.ui.status_gen_label.isEnabled():
    #                     self.ui.status_gen_label.setEnabled(False)
    #                     self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["error_a"])
    #                     self.ui.status_gen_label.setStyleSheet("color: red;")
    #                 else:
    #                     self.ui.status_gen_label.setEnabled(True)
    #                     self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["error_b"])
    #                     self.ui.status_gen_label.setStyleSheet("color: black;")
    #             else:
    #                 self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["connected"])
    #                 self.ui.status_gen_label.setStyleSheet("color: green;")

    def all_dev_connected_signal(self, opt_connected=False, ref_connected=False, gen_connected=False, gen_error=False,
                                 check_status=False, bad_ref=False):
        properties = ["opt_connected", "ref_connected", "gen_connected", "gen_error", "check_status", "bad_ref"]


        for prop, value in zip(properties,
                               [opt_connected, ref_connected, gen_connected, gen_error, check_status, bad_ref]):
            setattr(self, prop, value)

        enable_start_app = (
                ref_connected and opt_connected and gen_connected and
                self.ui.start_app.text() == self.translations[self.lang]["start_app_a"] and
                not gen_error and self.ui.combobox_sel_operator.currentIndex() != 0 and
                self.my_settings.opt_channels != 0 and not self.config_contains_none and not bad_ref
        )
        self.ui.start_app.setEnabled(enable_start_app)

        if check_status:
            label_config = [
                ("status_ref_label", ref_connected, not bad_ref, bad_ref),
                ("status_opt_label", opt_connected, True, False),
                ("status_gen_label", gen_connected, not gen_error, gen_error)
            ]

            for label, connected, condition_a, condition_b in label_config:
                label_widget = getattr(self.ui, label)
                translations = self.translations[self.lang][label]
                if connected:
                    label_widget.setText(translations["connected"])
                    label_widget.setStyleSheet("color: green;")
                else:
                    label_widget.setText(translations["disconnect"])
                    enabled = label_widget.isEnabled()
                    label_widget.setEnabled(not enabled)
                    label_widget.setStyleSheet("color: black;" if enabled else "color: red;")

                if label == "status_ref_label" and not connected:
                    self.check_devices_load_comboboxes()
                    self.ref_connected = False
                elif condition_b:
                    label_widget.setText(translations["wrong_name"])
                elif condition_a:
                    label_widget.setText(translations["disconnect"])

    def sens_type_combobox_changed(self, text):
        self.my_settings.opt_sensor_type = text
        self.config_file_path = self.check_config_if_selected()
        load_all_config_files(self.ui.opt_config_combobox, self.config_file_path, self.my_settings.opt_sensor_type,
                              self.my_settings.subfolderConfig_path)
        self.setup_config()

    def return_all_configs(self):
        from glob import glob
        yaml_files = glob(os_path.join(self.my_settings.subfolderConfig_path, '*.yaml'))
        yaml_return = []
        for yaml_file in yaml_files:
            try:
                config_file_path = os_path.join(self.my_settings.subfolderConfig_path, yaml_file)
                with open(config_file_path, 'r') as file:
                    config = yaml_safe_load(file)
                    if config['opt_measurement']['sensor_type'] == self.my_settings.opt_sensor_type:
                        yaml_return.append(yaml_file)
            except:
                continue
        return yaml_return

    def check_config_if_selected(self):
        yaml_files = self.return_all_configs()
        for yaml_file in yaml_files:
            config_file_path = os_path.join(self.my_settings.subfolderConfig_path, yaml_file)
            with open(config_file_path, 'r') as file:
                config = yaml_safe_load(file)
                if config['current']:
                    return config_file_path
        return None

    def setup_config(self):
        if self.config_file_path is not None and os_path.exists(self.config_file_path):
            self.config_contains_none = self.my_settings.load_config_file(self.config_file_path)
            self.check_devices_load_comboboxes()
        else:
            self.config_contains_none, self.config_file_path = self.my_settings.create_config_file()
            self.check_devices_load_comboboxes()

    def check_devices_load_comboboxes(self):
        self.ui.sens_type_comboBox.blockSignals(True)
        self.ui.opt_config_combobox.blockSignals(True)

        self.ui.sens_type_comboBox.clear()

        # load optical sensor types
        self.ui.sens_type_comboBox.addItem('Accelerometer')
        self.ui.sens_type_comboBox.addItem('Test')
        self.ui.sens_type_comboBox.setCurrentText(self.my_settings.opt_sensor_type)

        load_all_config_files(self.ui.opt_config_combobox, self.config_file_path, self.my_settings.opt_sensor_type,
                              self.my_settings.subfolderConfig_path)

        self.ui.sens_type_comboBox.blockSignals(False)
        self.ui.opt_config_combobox.blockSignals(False)

    def open_settings_window(self):
        from SensAcc.MySettingsWindow import MySettingsWindow
        self.settings_window = MySettingsWindow(True, self, self.my_settings)
        self.hide()

    def start_calib_app(self):
        self.ui.start_app.setStyleSheet("QPushButton:hover { background-color: none; }")
        self.ui.start_app.setEnabled(False)
        self.ui.start_app.setText(self.translations[self.lang]["start_app_b"])
        self.ui.opt_config_combobox.setEnabled(False)
        self.ui.sens_type_comboBox.setEnabled(False)
        self.ui.open_settings_btn.setEnabled(False)
        self.ui.combobox_sel_operator.setEnabled(False)
        self.ui.btn_add_operator.setEnabled(False)
        self.ui.menubar.setEnabled(False)
        QTimer.singleShot(100, self.after_delay)

    def after_delay(self):
        path_config = os_path.join(self.my_settings.folder_sentinel_D_folder, "config.ini")
        config = ConfigParser()
        with codecs_open(path_config, 'r', encoding='utf-8-sig') as f:
            config.read_file(f)
        config.set('general', 'export_folder_path', self.my_settings.folder_opt_export)
        with open(path_config, 'w') as configfile:
            config.write(configfile)
        start_sentinel_d(self.my_settings.opt_project, self.my_settings.folder_sentinel_D_folder, self.my_settings.subfolder_sentinel_project)
        self.operator = self.ui.combobox_sel_operator.currentText()

        # self.ui.ref_device_comboBox.setEnabled(False)

        self.thread_check_usb_devices.termination = True
        self.calib_window.first_sentinel_start(self.operator)
        self.ui.start_app.setText(self.translations[self.lang]["start_app_b"])
        self.check_last_calib()

    def show_back(self):
        self.set_language()
        if self.check_usbs_first_start:
            self.check_usbs_first_start = False
            from SensAcc.ThreadCheckDevicesConnected import ThreadCheckDevicesConnected
            self.thread_check_usb_devices = ThreadCheckDevicesConnected(self.opt_dev_vendor, self.ref_dev_vendor,
                                                                        self.my_settings)
            self.thread_check_usb_devices.all_connected.connect(self.all_dev_connected_signal)
            self.thread_check_usb_devices.start()

        self.setFixedSize(int(self.width()*self.window_scale_delta),
                          int(self.height()*self.window_scale_delta))
        scale_app(self, self.window_scale_delta)
        self.window_scale_delta = 1
        self.check_devices_load_comboboxes()
        if self.operator:
            self.load_operators(self.operator)
        else:
            self.load_operators()

        QTimer.singleShot(0, lambda: center_on_screen(self))

    def showEvent(self, a0):
        if self.calib_window is None:
            from SensAcc.MyMainWindow import MyMainWindow
            self.calib_window = MyMainWindow(self, self.my_settings, self.thcfgs)
            self.splash.hide()

    def closeEvent(self, event):
        box = QMessageBox(self)
        box.setWindowTitle(self.translations[self.lang]['close_event_a'])
        box.setText(self.translations[self.lang]['close_event_b'])

        yes_button = box.addButton(self.translations[self.lang]['close_event_yes'], QMessageBox.YesRole)
        no_button = box.addButton(self.translations[self.lang]['close_event_no'], QMessageBox.NoRole)

        box.exec_()

        if box.clickedButton() == yes_button:
            self.thread_check_usb_devices.termination = True
            self.thread_check_usb_devices.wait()
            event.accept()
        else:
            event.ignore()

    def set_language(self):
        file_path = "lang_pack.json"
        with open(file_path, 'r', encoding="utf-8") as f:
            self.translations = json_load(f)
        if self.calib_window is None:
            self.ui.sens_type_label.setText(self.translations[self.lang]["sens_type_label"])
            self.ui.status_opt_label.setText(self.translations[self.lang]["status_opt_label"]["init"])
            self.ui.status_label.setText(self.translations[self.lang]["status_label"])
            self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["init"])
            self.ui.opt_channel_label.setText(self.translations[self.lang]["opt_channel_label"])
            self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["init"])
            self.ui.start_app.setText(self.translations[self.lang]["start_app_a"])
            self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])

    def load_global_settings(self):
        with open("global_settings.yaml", 'r') as file:
            config = yaml_safe_load(file)
        self.version = config["version"]
        self.lang = config["language"]
        self.window_scale = config["windows_scale"]
        self.last_ref_calib = config["last_ref_calib"]
        self.calib_treshold = int(config["treshold"])

    def check_last_calib(self, get_bool=False):

        def show_warning(last_date):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(self.translations[self.lang]["last_calib_warn"])
            msg.setText(f"{self.translations[self.lang]['last_calib_warn_text']}{last_date}.")
            msg.addButton('OK', QMessageBox.AcceptRole)
            msg.exec_()
        if self.last_ref_calib:
            import datetime
            last_calib = None
            if isinstance(self.last_ref_calib, datetime.date):
                last_calib = QDate(self.last_ref_calib.year, self.last_ref_calib.month, self.last_ref_calib.day)

            elif isinstance(self.last_ref_calib, str):
                year, month, day = map(int, self.last_ref_calib.split('-'))
                last_calib = QDate(year, month, day)

            current_date = QDate.currentDate()
            if last_calib:
                days_apart = last_calib.daysTo(current_date)
                if days_apart > self.calib_treshold:
                    if not get_bool:
                        show_warning(last_calib.toString("yyyy-MM-dd"))
                        return
                    return True
                else:
                    return False
