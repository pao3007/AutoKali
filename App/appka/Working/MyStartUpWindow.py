from PyQt5.QtCore import QTimer, QDate
from PyQt5.QtGui import QPixmap
from codecs import open as codecs_open
from configparser import ConfigParser
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QSplashScreen
from yaml import safe_load as yaml_safe_load, safe_dump as yaml_safe_dump
from os import path as os_path, getcwd as os_getcwd
from gui.start_up import Ui_Setup
from definitions import scale_app, center_on_screen, load_all_config_files, show_add_dialog
from acc.ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from acc.SettingsParams import MySettings
from json import load as json_load


class MyStartUpWindow(QMainWindow):

    def __init__(self, splash: QSplashScreen):
        super().__init__()
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
        # self.ui.ref_channel_comboBox.currentTextChanged.connect(self.ref_channel_combobox_changed)
        # self.ui.ref_device_comboBox.currentTextChanged.connect(self.ref_device_combobox_changed)
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
        self.splash.hide()
        scale_app(self, self.window_scale)
        self.setFixedSize(int(self.width() * self.window_scale),
                          int(self.height() * self.window_scale))
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
        self.all_dev_connected_signal(combobox=True)

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

    def all_dev_connected_signal(self, opt_connected=False, ref_connected=False, gen_connected=False, gen_error=False, check_status=False, bad_ref=False, combobox=False):
        if combobox and self.opt_connected is not None:
            opt_connected = self.opt_connected
            ref_connected = self.ref_connected
            gen_connected = self.gen_connected
            gen_error = self.gen_error
            check_status = self.check_status
            bad_ref = self.bad_ref
        else:
            self.opt_connected = opt_connected
            self.ref_connected = ref_connected
            self.gen_connected = gen_connected
            self.gen_error = gen_error
            self.check_status = check_status
            self.bad_ref = bad_ref
        ow = False
        if (ref_connected and opt_connected and gen_connected and self.ui.start_app.text() == self.translations[self.lang]["start_app_a"] and not gen_error and
                self.ui.combobox_sel_operator.currentIndex() != 0 and self.my_settings.opt_channels != 0 and not self.config_contains_none and not bad_ref) or ow:
            self.ui.start_app.setEnabled(True)
        else:
            self.ui.start_app.setEnabled(False)

        if check_status:
            if not self.config_contains_none:
                self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
                self.ui.open_settings_btn.setStyleSheet("color: black;")
            if self.config_contains_none and not ow:
                if self.ui.null_detect_label.isEnabled():
                    # self.ui.null_detect_label.setHidden(False)
                    self.ui.null_detect_label.setEnabled(False)
                    # self.ui.null_detect_label.setStyleSheet("color: black;")
                    self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
                    self.ui.open_settings_btn.setStyleSheet("color: red;")
                else:
                    # self.ui.null_detect_label.setHidden(False)
                    self.ui.null_detect_label.setEnabled(True)
                    # self.ui.null_detect_label.setStyleSheet("color: red;")
                    self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn_err"])
                    self.ui.open_settings_btn.setStyleSheet("color: red;")
                self.ui.start_app.setEnabled(False)
            # elif self.my_settings.opt_channels != 0:
            #     self.ui.null_detect_label.setHidden(True)
            #     if ref_connected and opt_connected and gen_connected and self.ui.start_app.text() == "START" and not gen_error and (self.ui.combobox_sel_operator.currentIndex() != 0) or ow:
            #         self.ui.start_app.setEnabled(True)

            if not ref_connected and not bad_ref:
                self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["disconnect"])
                if self.ui.status_ref_label.isEnabled():
                    self.ui.status_ref_label.setEnabled(False)
                    self.ui.status_ref_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_ref_label.setEnabled(True)
                    self.ui.status_ref_label.setStyleSheet("color: red;")
                if self.ref_connected:
                    self.check_devices_load_comboboxes()
                    self.ref_connected = False
            elif bad_ref:
                self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["wrong_name"])
                if self.ui.status_ref_label.isEnabled():
                    self.ui.status_ref_label.setEnabled(False)
                    self.ui.status_ref_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_ref_label.setEnabled(True)
                    self.ui.status_ref_label.setStyleSheet("color: red;")
                if self.ref_connected:
                    self.check_devices_load_comboboxes()
                    self.ref_connected = False
            else:
                self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["connected"])
                self.ui.status_ref_label.setStyleSheet("color: green;")
                if not self.ref_connected:
                    self.ref_connected = True
                    self.check_devices_load_comboboxes()

            if not opt_connected:
                self.ui.status_opt_label.setText(self.translations[self.lang]["status_opt_label"]["disconnect"])
                if self.ui.status_opt_label.isEnabled():
                    self.ui.status_opt_label.setEnabled(False)
                    self.ui.status_opt_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_opt_label.setEnabled(True)
                    self.ui.status_opt_label.setStyleSheet("color: red;")
            else:
                self.ui.status_opt_label.setText(self.translations[self.lang]["status_opt_label"]["connected"])
                self.ui.status_opt_label.setStyleSheet("color: green;")

            if not gen_connected:
                self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["disconnect"])
                if self.ui.status_gen_label.isEnabled():
                    self.ui.status_gen_label.setEnabled(False)
                    self.ui.status_gen_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_gen_label.setEnabled(True)
                    self.ui.status_gen_label.setStyleSheet("color: red;")
            else:
                if gen_error:
                    if self.ui.status_gen_label.isEnabled():
                        self.ui.status_gen_label.setEnabled(False)
                        self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["error_a"])
                        self.ui.status_gen_label.setStyleSheet("color: red;")
                    else:
                        self.ui.status_gen_label.setEnabled(True)
                        self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["error_b"])
                        self.ui.status_gen_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_gen_label.setText(self.translations[self.lang]["status_gen_label"]["connected"])
                    self.ui.status_gen_label.setStyleSheet("color: green;")

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
        # self.ui.ref_device_comboBox.blockSignals(True)
        # self.ui.ref_channel_comboBox.blockSignals(True)
        self.ui.sens_type_comboBox.blockSignals(True)
        self.ui.opt_config_combobox.blockSignals(True)

        # self.ui.ref_device_comboBox.clear()
        # self.ui.ref_channel_comboBox.clear()
        self.ui.sens_type_comboBox.clear()

        # load optical sensor types
        self.ui.sens_type_comboBox.addItem('Accelerometer')
        self.ui.sens_type_comboBox.addItem('Test')
        self.ui.sens_type_comboBox.setCurrentText(self.my_settings.opt_sensor_type)

        # load ref sens devices
        # system = nidaqmx_system.System.local()
        # for device in system.devices:
        #     # self.ui.ref_device_comboBox.addItem(f'{device.name}')
        # if self.my_settings.ref_device_name is not None and self.ui.ref_device_comboBox.count() != 0:
        #     self.ui.ref_device_comboBox.setCurrentText(self.my_settings.ref_device_name)
        # else:
        #     self.ui.ref_device_comboBox.addItem('NOT DETECTED')
        #     self.ui.ref_device_comboBox.setCurrentText("NOT DETECTED")

        # load ref sens channels
        # self.ui.ref_channel_comboBox.addItem('ai0')
        # self.ui.ref_channel_comboBox.addItem('ai1')
        # self.ui.ref_channel_comboBox.addItem('ai2')

        # if self.my_settings.ref_channel is not None:
        #     self.ui.ref_channel_comboBox.setCurrentText(self.my_settings.ref_channel)

        load_all_config_files(self.ui.opt_config_combobox, self.config_file_path, self.my_settings.opt_sensor_type,
                              self.my_settings.subfolderConfig_path)

        # self.ui.ref_device_comboBox.blockSignals(False)
        # self.ui.ref_channel_comboBox.blockSignals(False)
        self.ui.sens_type_comboBox.blockSignals(False)
        self.ui.opt_config_combobox.blockSignals(False)

    def open_settings_window(self):
        from acc.MySettingsWindow import MySettingsWindow
        self.settings_window = MySettingsWindow(True, self, self.my_settings)
        self.hide()

    def start_calib_app(self):
        from acc.MyMainWindow import MyMainWindow
        path_config = os_path.join(self.my_settings.folder_sentinel_D_folder, "config.ini")
        config = ConfigParser()
        with codecs_open(path_config, 'r', encoding='utf-8-sig') as f:
            config.read_file(f)
        config.set('general', 'export_folder_path', self.my_settings.folder_opt_export)
        with open(path_config, 'w') as configfile:
            config.write(configfile)

        # self.ui.ref_device_comboBox.setEnabled(False)
        self.ui.opt_config_combobox.setEnabled(False)
        # self.ui.ref_channel_comboBox.setEnabled(False)
        self.ui.sens_type_comboBox.setEnabled(False)
        self.ui.open_settings_btn.setEnabled(False)
        self.ui.combobox_sel_operator.setEnabled(False)
        self.ui.btn_add_operator.setEnabled(False)
        self.operator = self.ui.combobox_sel_operator.currentText()
        self.ui.menubar.setEnabled(False)
        self.ui.start_app.setText(self.translations[self.lang]["start_app_b"])
        self.ui.start_app.setEnabled(False)
        self.thread_check_usb_devices.termination = True
        self.calib_window = MyMainWindow(self, self.my_settings, self.thcfgs)
        self.calib_window.first_sentinel_start()
        self.check_last_calib()

    def show_back(self):
        self.set_language()
        if self.check_usbs_first_start:
            self.check_usbs_first_start = False
            from acc.ThreadCheckDevicesConnected import ThreadCheckDevicesConnected
            self.thread_check_usb_devices = ThreadCheckDevicesConnected(self.opt_dev_vendor, self.ref_dev_vendor,
                                                                        self.my_settings)
            self.thread_check_usb_devices.all_connected.connect(self.all_dev_connected_signal)
            self.thread_check_usb_devices.start()

        self.setFixedSize(int(self.width()*self.window_scale_delta),
                          int(self.height()*self.window_scale_delta))
        scale_app(self, self.window_scale_delta)
        self.window_scale_delta = 1
        self.check_devices_load_comboboxes()
        print(str(self.config_contains_none) + " <-- self.config_contains_none")
        if self.operator:
            self.load_operators(self.operator)
        else:
            self.load_operators()

        def get_font_params(qfont):
            font_params = {
                "Family": qfont.family(),
                "PointSize": qfont.pointSize(),
                "PixelSize": qfont.pixelSize(),
                "Weight": qfont.weight(),
                "Bold": qfont.bold(),
                "Italic": qfont.italic(),
                "Underline": qfont.underline(),
                "StrikeOut": qfont.strikeOut(),
                "Kerning": qfont.kerning(),
                "Style": qfont.style(),
                "FixedPitch": qfont.fixedPitch(),
                "Stretch": qfont.stretch(),
                "LetterSpacing": qfont.letterSpacing(),
                "LetterSpacingType": qfont.letterSpacingType(),
                "WordSpacing": qfont.wordSpacing(),
                "Capitalization": qfont.capitalization(),
                "HintingPreference": qfont.hintingPreference()
            }
            return font_params
        # def bad_scales():
        #
        #     font = self.ui.combobox_sel_operator.font()
        #     params = get_font_params(font)
        #     for key, value in params.items():
        #         print(f"{key}: {value}")
        #     # font.setPointSizeF((7 * self.window_scale))
        #     # self.ui.combobox_sel_operator.setFont(font)
        #
        #     font = self.ui.opt_config_combobox.font()
        #     font.setPointSizeF((8 * self.window_scale))
        #     self.ui.opt_config_combobox.setFont(font)
        #
        #     font = self.ui.sens_type_comboBox.font()
        #     font.setPointSizeF((8 * self.window_scale))
        #     self.ui.sens_type_comboBox.setFont(font)
        #
        #     font = self.ui.btn_add_operator.font()
        #     font.setPointSizeF((8 * self.window_scale))
        #     self.ui.btn_add_operator.setFont(font)
        # bad_scales()
        QTimer.singleShot(0, lambda: center_on_screen(self))

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
