from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from codecs import open as codecs_open
from configparser import ConfigParser
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QSplashScreen, QDialog, QVBoxLayout, QLineEdit, QDialogButtonBox
from yaml import safe_load as yaml_safe_load, dump as yaml_dump, safe_dump as yaml_safe_dump
from nidaqmx import system as nidaqmx_system
from os import path as os_path, getcwd as os_getcwd
from start_up import Ui_Setup
from definitions import scale_app, center_on_screen, load_all_config_files
from ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from SettingsParams import MySettings


class MyStartUpWindow(QMainWindow):

    def __init__(self, splash: QSplashScreen):
        super().__init__()

        self.thread_check_usb_devices = None
        self.splash = splash
        self.thcfgs = ThreadControlFuncGenStatements()
        self.window_scale_delta = 1
        self.window_scale = 1
        self.yaml_devices_vendor = 'devices_vendor_ids.yaml'
        
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

        self.config = None
        self.config_contains_none = True

        self.ui = Ui_Setup()
        self.ui.setupUi(self)
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
        self.ui.status_opt_label.setText("Optical device INIT")
        self.ui.status_opt_label.setStyleSheet("color: black;")
        self.ui.status_ref_label.setText("Reference device INIT")
        self.ui.status_ref_label.setStyleSheet("color: black;")
        self.ui.status_gen_label.setText("Function generator INIT")
        self.ui.status_gen_label.setStyleSheet("color: black;")
        self.ui.open_settings_btn.setText("SETTINGS")
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
        self.show()

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
            msgBox = QMessageBox()
            msgBox.setText(f"Do you really want to remove the operator? : {op_to_remv}")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            ret = msgBox.exec_()

            if ret == QMessageBox.Yes:
                load_and_delete_operator(op_to_remv)
                self.load_operators()
                self.operator_changed(0)
                print("Operator removed")
                # Logic to remove operator here

        def show_add_dialog():
            def add_operator_to_yaml(new_operator, file_path="operators.yaml"):
                try:
                    # Read the existing YAML file
                    with open(file_path, 'r') as f:
                        data = yaml_safe_load(f)

                    # Check if 'operators' key exists in the YAML, if not create one
                    if 'operators' not in data:
                        data['operators'] = []

                    # Add the new operator to the list of operators
                    data['operators'].append(new_operator)

                    # Write the updated data back to the YAML file
                    with open(file_path, 'w') as f:
                        yaml_safe_dump(data, f)

                    print(f"Added {new_operator} to {file_path}")
                    self.load_operators(select_operator=new_operator)
                except Exception as e:
                    print(f"An error occurred: {e}")

            dialog = QDialog(self)
            dialog.setWindowTitle("Add New Operator")
            dialog_layout = QVBoxLayout()

            line_edit = QLineEdit()
            dialog_layout.addWidget(line_edit)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            dialog_layout.addWidget(button_box)

            dialog.setLayout(dialog_layout)

            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)

            result = dialog.exec_()

            if result == QDialog.Accepted:
                add_operator_to_yaml(line_edit.text())

        if self.ui.combobox_sel_operator.currentIndex() != 0:
            print("remove")
            show_remove_dialog()
        else:
            print("add")
            show_add_dialog()

    def load_operators(self, select_operator = None):
        self.ui.combobox_sel_operator.blockSignals(True)
        self.ui.combobox_sel_operator.clear()
        self.ui.combobox_sel_operator.addItem("Select/Add operator")
        file_path = "operators.yaml"
        try:
            with open(file_path, 'r') as f:
                data = yaml_safe_load(f)
            operators = data.get('operators', [])
            for operator in operators:
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

    def all_dev_connected_signal(self, opt_connected, ref_connected, gen_connected, gen_error, check_status):
        ow = False
        if (ref_connected and opt_connected and gen_connected and self.ui.start_app.text() == "START" and not gen_error and
                self.ui.combobox_sel_operator.currentIndex() != 0 and self.my_settings.opt_channels != 0 and not self.config_contains_none) or ow:
            self.ui.start_app.setEnabled(True)
        else:
            self.ui.start_app.setEnabled(False)

        if check_status:
            if not self.config_contains_none:
                self.ui.open_settings_btn.setText("SETTINGS")
                self.ui.open_settings_btn.setStyleSheet("color: black;")
            if self.config_contains_none and not ow:
                if self.ui.null_detect_label.isEnabled():
                    # self.ui.null_detect_label.setHidden(False)
                    self.ui.null_detect_label.setEnabled(False)
                    # self.ui.null_detect_label.setStyleSheet("color: black;")
                    self.ui.open_settings_btn.setText("SETTINGS")
                    self.ui.open_settings_btn.setStyleSheet("color: red;")
                else:
                    # self.ui.null_detect_label.setHidden(False)
                    self.ui.null_detect_label.setEnabled(True)
                    # self.ui.null_detect_label.setStyleSheet("color: red;")
                    self.ui.open_settings_btn.setText("SETUP     ")
                    self.ui.open_settings_btn.setStyleSheet("color: red;")
                self.ui.start_app.setEnabled(False)
            # elif self.my_settings.opt_channels != 0:
            #     self.ui.null_detect_label.setHidden(True)
            #     if ref_connected and opt_connected and gen_connected and self.ui.start_app.text() == "START" and not gen_error and (self.ui.combobox_sel_operator.currentIndex() != 0) or ow:
            #         self.ui.start_app.setEnabled(True)


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

            if not gen_connected:
                self.ui.status_gen_label.setText("Function generator DISCONNECTED")
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
                        self.ui.status_gen_label.setText("Function generator ERROR")
                        self.ui.status_gen_label.setStyleSheet("color: red;")
                    else:
                        self.ui.status_gen_label.setEnabled(True)
                        self.ui.status_gen_label.setText("please RESTART generator")
                        self.ui.status_gen_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_gen_label.setText("Function generator CONNECTED")
                    self.ui.status_gen_label.setStyleSheet("color: green;")

    def sens_type_combobox_changed(self, text):
        self.my_settings.opt_sensor_type = text
        self.config_file_path = self.check_config_if_selected()
        load_all_config_files(self.ui.opt_config_combobox, self.config_file_path, self.my_settings.opt_sensor_type,
                              self.my_settings.subfolderConfig_path)
        self.setup_config()

        # self.save_config_file(True)

    # def ref_channel_combobox_changed(self, text):
    #     self.my_settings.ref_channel = text
    #     self.config_contains_none = self.my_settings.save_config_file(True, self.config_file_path)

    # def ref_device_combobox_changed(self, text):
    #     if text != "NOT DETECTED":
    #         self.my_settings.ref_device_name = text
    #     self.config_contains_none = self.my_settings.save_config_file(True,self.config_file_path)

    def return_all_configs(self):
        from glob import glob
        yaml_files = glob(os_path.join(self.my_settings.subfolderConfig_path, '*.yaml'))
        yaml_return = []
        for yaml_file in yaml_files:
            config_file_path = os_path.join(self.my_settings.subfolderConfig_path, yaml_file)
            with open(config_file_path, 'r') as file:
                config = yaml_safe_load(file)
                if config['opt_measurement']['sensor_type'] == self.my_settings.opt_sensor_type:
                    yaml_return.append(yaml_file)
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
        from MySettingsWindow import MySettingsWindow
        self.settings_window = MySettingsWindow(True, self, self.my_settings)
        self.hide()

    def start_calib_app(self):
        from MyMainWindow import MyMainWindow
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
        self.ui.start_app.setText("STARTING")
        self.ui.start_app.setEnabled(False)
        self.thread_check_usb_devices.termination = True
        self.calib_window = MyMainWindow(self, self.my_settings, self.thcfgs)
        self.calib_window.first_sentinel_start()

    def showEvent(self, event):
        if self.check_usbs_first_start:
            self.check_usbs_first_start = False
            from ThreadCheckDevicesConnected import ThreadCheckDevicesConnected
            self.thread_check_usb_devices = ThreadCheckDevicesConnected(self.opt_dev_vendor, self.ref_dev_vendor,
                                                                        self.my_settings)
            self.thread_check_usb_devices.all_connected.connect(self.all_dev_connected_signal)
            self.thread_check_usb_devices.start()

        self.setFixedSize(int(self.width()*self.window_scale_delta),
                          int(self.height()*self.window_scale_delta))
        scale_app(self, self.window_scale_delta)
        self.window_scale_delta = 1
        center_on_screen(self)
        self.check_devices_load_comboboxes()
        print(str(self.config_contains_none) + " <-- self.config_contains_none")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirmation',
                                     "Are you sure you want to exit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.thread_check_usb_devices.termination = True
            self.thread_check_usb_devices.wait()
            event.accept()
        else:
            event.ignore()
