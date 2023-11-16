from PyQt5.QtCore import QTimer, QDate, Qt
from PyQt5.QtGui import QPixmap
from codecs import open as codecs_open
from configparser import ConfigParser
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QSplashScreen
from yaml import safe_load as yaml_safe_load, safe_dump as yaml_safe_dump
from os import path as os_path, getcwd as os_getcwd
from gui.start_up import Ui_Setup
from definitions import scale_app, center_on_screen, load_all_config_files, kill_sentinel
from SensAcc.SettingsParams import MySettings
from SensStrain.SettingsParams import MySettings as MySettings_strain
from json import load as json_load
from definitions import start_sentinel_d


class MyStartUpWindow(QMainWindow):
    """SK: Trieda ktorá nám vytvorí úvodné okno, kontrolujeme stav pripojených nastavení,
    voľba typu senzora a konfiguračného súboru pre senzor, možnosť otvoriť nastavenia, výber/úprava operátorov.
    EN: A class that creates the initial window, checks the status of connected settings,
    selects the type of sensor and the configuration file for the sensor, offers the option to open settings,
    and the selection/editing of operators"""
    def __init__(self, splash: QSplashScreen):
        super().__init__()

        def connect_set_buttons():
            self.ui.start_app.setEnabled(False)
            self.ui.open_settings_btn.clicked.connect(self.open_settings_window)
            self.ui.start_app.clicked.connect(self.start_calib_app)
            self.ui.btn_add_operator.clicked.connect(self.add_remove_operator)

        def connect_combo_boxes():
            self.ui.sens_type_comboBox.currentTextChanged.connect(self.sens_type_combobox_changed)
            self.ui.opt_config_combobox.currentTextChanged.connect(self.config_combobox_changed)
            self.ui.combobox_sel_operator.currentIndexChanged.connect(self.operator_changed)

        def load_images_icons():
            self.ui.logo_label.setPixmap(QPixmap("images/logo.png"))
            icon = QIcon(QPixmap("images/setting_btn.png"))
            self.ui.open_settings_btn.setIcon(icon)
            self.ui.open_settings_btn.setIconSize(self.ui.open_settings_btn.sizeHint())
            self.ui.open_settings_btn.setStyleSheet("text-align: center;")
            self.setWindowIcon(QIcon('images/logo_icon.png'))

        def setup_window():
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowMaximizeButtonHint)
            self.setWindowTitle("Appka")
            self.setFixedSize(self.width(), int(self.height() * 0.95))
            scale_app(self, self.window_scale)
            self.setFixedSize(int(self.width() * self.window_scale),
                              int(self.height() * self.window_scale))

        def set_labels():
            self.ui.null_detect_label.setHidden(True)
            self.ui.status_opt_label.setStyleSheet("color: black;")
            self.ui.status_ref_label.setStyleSheet("color: black;")
            self.ui.status_gen_label.setStyleSheet("color: black;")
            self.ui.open_settings_btn.setStyleSheet("color: black;")

        self.block_status_update = False
        self.my_main_window_strain = None
        self.my_main_window_acc = None
        self.my_settings_window_strain = None
        self.my_settings_window_acc = None
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
        self.sens_type = None
        self.starting_folder = os_getcwd()
        self.my_settings = MySettings(self.starting_folder)

        self.load_global_settings()

        self.config = None
        self.config_contains_none = True

        self.ui = Ui_Setup()
        self.ui.setupUi(self)

        self.set_language()
        connect_set_buttons()
        connect_combo_boxes()
        self.load_operators()
        set_labels()
        load_images_icons()

        self.config_file_path = self.check_config_if_selected()
        self.check_devices_load_comboboxes_load_config_file()
        self.load_usb_dev_vendors()
        setup_window()
        kill_sentinel(True, True)
        self.show_back()

    def add_remove_operator(self):
        """SK: Funkcia na prídavanie/vymazanie operátora do/z listu operátorov, vytvorenie pop-up okna na
        interakciu s uživateľom.
        EN:Function for adding/deleting an operator to/from the list of operators, creating a pop-up window for
        interaction with the user"""
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
                    from definitions import save_error
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
            from definitions import show_add_dialog
            show_add_dialog(self, self.starting_folder)

    def load_operators(self, select_operator=None):
        """SK: Funkcia ktorá načítava operátorov z yaml súboru.
        EN: A function that loads operators from a YAML file."""
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
        """SK: Funkcia ktorá pri zmene operátora (combobox) uloží vybraného operátora a následne vykoná kontrolu
        či sa štart tlačidlo povolí.
        EN: A function that, upon changing the operator (combobox), saves the selected operator and then performs
        a check to determine if the start button is enabled."""
        self.operator = self.ui.combobox_sel_operator.itemText(idx)
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
        """SK: Funckia ktorá pri zmene konfiguračného súboru pre senzor, načíta zvolený konfiguračný súbor a
        vykoná kontrolu či sú všetky parametre riadne vyplnené.
        EN: A function that, upon changing the configuration file for a sensor, loads the selected configuration file and
        performs a check to ensure that all parameters are properly filled out."""
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
            self.check_devices_load_comboboxes_load_config_file()
            self.current_conf = True
            self.config_contains_none = self.my_settings.save_config_file(True, self.config_file_path)
        except Exception as e:
            print(e)

    def load_usb_dev_vendors(self):
        """SK: Funkcia slúži na načítanie VID alebo PID pre používané zariadenia, ktoré sa používajú pri kontrole.
        EN: A function for loading the VID or PID for devices used in check."""
        config_file_path = os_path.join(self.starting_folder, self.yaml_devices_vendor)
        with open(config_file_path, 'r') as file:
            data = yaml_safe_load(file)

        self.opt_dev_vendor = data[self.ui.sens_type_comboBox.currentText()]['optical']
        self.ref_dev_vendor = data[self.ui.sens_type_comboBox.currentText()]['reference']

    def all_dev_connected_signal_strain(self, opt_connected=False, ref_connected=False, check_status=False):
        """SK: Funkcia kontroluje pripojené zariadenia pre strain kalibráciu a upravuje status pre dané zariadenie pre
        interakciu s uživateľom.
        EN: A function that checks connected devices for strain calibration and modifies the status for a given device for
        interaction with the user."""
        self.opt_connected = opt_connected
        self.ref_connected = ref_connected
        self.gen_connected = True

        if not self.block_status_update:
            ow = True
            if (ref_connected and opt_connected and self.ui.start_app.text() == self.translations[self.lang]["start_app_a"] and
                    self.ui.combobox_sel_operator.currentIndex() != 0 and self.my_settings.opt_channels != 0 and not self.config_contains_none) or ow:
                self.ui.start_app.setEnabled(True)
            else:
                self.ui.start_app.setEnabled(False)
            self.ui.status_ref_label.setText("...")
            self.ui.status_ref_label.setStyleSheet("color: black;")
            if check_status:
                # print(self.config_contains_none)
                if not self.config_contains_none:
                    self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
                    self.ui.open_settings_btn.setStyleSheet("color: black;")
                if self.config_contains_none:
                    if self.ui.null_detect_label.isEnabled():

                        self.ui.null_detect_label.setEnabled(False)

                        self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
                        self.ui.open_settings_btn.setStyleSheet("color: red;")
                    else:

                        self.ui.null_detect_label.setEnabled(True)

                        self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
                        self.ui.open_settings_btn.setStyleSheet("color: black;")
                if not ref_connected:
                    self.ui.status_gen_label.setText(self.translations[self.lang]["status_ref_label_benchtop"]["disconnect"])
                    if self.ui.status_gen_label.isEnabled():
                        self.ui.status_gen_label.setEnabled(False)
                        self.ui.status_gen_label.setStyleSheet("color: black;")
                    else:
                        self.ui.status_gen_label.setEnabled(True)
                        self.ui.status_gen_label.setStyleSheet("color: red;")
                    if self.ref_connected:
                        self.check_devices_load_comboboxes_load_config_file()
                        self.ref_connected = False
                else:
                    self.ui.status_gen_label.setText(self.translations[self.lang]["status_ref_label_benchtop"]["connected"])
                    self.ui.status_gen_label.setStyleSheet("color: green;")
                    if not self.ref_connected:
                        self.ref_connected = True
                        self.check_devices_load_comboboxes_load_config_file()

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

    # def all_dev_connected_signal(self, opt_connected=False, ref_connected=False, gen_connected=False, gen_error=False,
    #                              check_status=False, bad_ref=False):
    #
    #     properties = ["opt_connected", "ref_connected", "gen_connected", "gen_error", "check_status", "bad_ref"]
    #
    #     for prop, value in zip(properties,
    #                            [opt_connected, ref_connected, gen_connected, gen_error, check_status, bad_ref]):
    #         setattr(self, prop, value)
    #     if not self.block_status_update:
    #         enable_start_app = (
    #                 ref_connected and opt_connected and gen_connected and
    #                 self.ui.start_app.text() == self.translations[self.lang]["start_app_a"] and
    #                 not gen_error and self.ui.combobox_sel_operator.currentIndex() != 0 and
    #                 self.my_settings.opt_channels != 0 and not self.config_contains_none and not bad_ref
    #         )
    #         self.ui.start_app.setEnabled(enable_start_app)
    #
    #         if check_status:
    #             if not self.config_contains_none:
    #                 self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
    #                 self.ui.open_settings_btn.setStyleSheet("color: black;")
    #             if self.config_contains_none:
    #                 if self.ui.null_detect_label.isEnabled():
    #
    #                     self.ui.null_detect_label.setEnabled(False)
    #
    #                     self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
    #                     self.ui.open_settings_btn.setStyleSheet("color: red;")
    #                 else:
    #
    #                     self.ui.null_detect_label.setEnabled(True)
    #
    #                     self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
    #                     self.ui.open_settings_btn.setStyleSheet("color: black;")
    #             label_config = [
    #                 ("status_ref_label", ref_connected, not bad_ref, bad_ref),
    #                 ("status_opt_label", opt_connected, True, False),
    #                 ("status_gen_label", gen_connected, not gen_error, gen_error)
    #             ]
    #
    #             for label, connected, condition_a, condition_b in label_config:
    #                 label_widget = getattr(self.ui, label)
    #                 translations = self.translations[self.lang][label]
    #                 if connected:
    #                     label_widget.setText(translations["connected"])
    #                     label_widget.setStyleSheet("color: green;")
    #                 else:
    #                     label_widget.setText(translations["disconnect"])
    #                     enabled = label_widget.isEnabled()
    #                     label_widget.setEnabled(not enabled)
    #                     label_widget.setStyleSheet("color: black;" if enabled else "color: red;")
    #
    #                 if label == "status_ref_label" and not connected:
    #                     # self.check_devices_load_comboboxes()
    #                     self.ref_connected = False
    #                 elif condition_b and label == "status_ref_label":
    #                     label_widget.setText(translations["wrong_name"])
    #                 elif condition_a and label == "status_ref_label":
    #                     label_widget.setText(translations["disconnect"])

    def all_dev_connected_signal(self, opt_connected=False, ref_connected=False, gen_connected=False, gen_error=False,
                                 check_status=False, bad_ref=False):
        """SK: Funkcia kontroluje pripojené zariadenia pre acc kalibráciu a upravuje status pre dané zariadenie pre
        interakciu s uživateľom.
        EN: A function that checks connected devices for acc calibration and modifies the status for a given device for
        interaction with the user."""
        self.opt_connected = opt_connected
        self.ref_connected = ref_connected
        self.gen_connected = gen_connected
        self.gen_error = gen_error
        self.check_status = check_status
        self.bad_ref = bad_ref
        ow = False
        if (ref_connected and opt_connected and gen_connected and self.ui.start_app.text() ==
            self.translations[self.lang]["start_app_a"] and not gen_error and
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

                    self.ui.null_detect_label.setEnabled(False)

                    self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn"])
                    self.ui.open_settings_btn.setStyleSheet("color: red;")
                else:

                    self.ui.null_detect_label.setEnabled(True)

                    self.ui.open_settings_btn.setText(self.translations[self.lang]["open_settings_btn_err"])
                    self.ui.open_settings_btn.setStyleSheet("color: red;")
                self.ui.start_app.setEnabled(False)

            if not ref_connected and not bad_ref:
                self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["disconnect"])
                if self.ui.status_ref_label.isEnabled():
                    self.ui.status_ref_label.setEnabled(False)
                    self.ui.status_ref_label.setStyleSheet("color: black;")
                else:
                    self.ui.status_ref_label.setEnabled(True)
                    self.ui.status_ref_label.setStyleSheet("color: red;")
                if self.ref_connected:
                    self.check_devices_load_comboboxes_load_config_file()
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
                    self.check_devices_load_comboboxes_load_config_file()
                    self.ref_connected = False
            else:
                self.ui.status_ref_label.setText(self.translations[self.lang]["status_ref_label"]["connected"])
                self.ui.status_ref_label.setStyleSheet("color: green;")
                if not self.ref_connected:
                    self.ref_connected = True
                    self.check_devices_load_comboboxes_load_config_file()

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
        """SK: Funkcia načíta všetky konfiguračné súbory, VID a PID pre daný/zvolený typ senzora a načíta posledne použitý
        konfiguračný súbor.
        EN: A function that loads all configuration files, VID, and PID for a given/selected type of sensor, and loads the
        last used configuration file."""
        self.opt_connected = False
        self.ref_connected = False
        self.gen_connected = False
        self.ui.start_app.setEnabled(False)
        self.load_usb_dev_vendors()
        self.my_settings.opt_sensor_type = text
        self.sens_type = text
        self.config_file_path = self.check_config_if_selected()
        print(self.config_file_path)
        load_all_config_files(self.ui.opt_config_combobox, self.config_file_path, self.sens_type,
                              self.my_settings.subfolderConfig_path)

        self.check_devices_load_comboboxes_load_config_file()

    def return_all_configs(self):
        """SK: Funkcia vracia všetky konfiguračné súbory pre daný typ senzora.
        EN: A function that returns all configuration files for a given type of sensor."""
        from glob import glob
        yaml_files = glob(os_path.join(self.my_settings.subfolderConfig_path, '*.yaml'))
        yaml_return = []
        for yaml_file in yaml_files:
            try:
                config_file_path = os_path.join(self.my_settings.subfolderConfig_path, yaml_file)
                with open(config_file_path, 'r') as file:
                    config = yaml_safe_load(file)
                    if config['opt_measurement']['sensor_type'] == self.sens_type:
                        yaml_return.append(yaml_file)
            except:
                continue
        return yaml_return

    def check_config_if_selected(self):
        """SK: Funkcia nám vracia posledný použitý konfiguračný súbor.
        EN: A function that returns the last used configuration file."""
        yaml_files = self.return_all_configs()
        for yaml_file in yaml_files:
            config_file_path = os_path.join(self.my_settings.subfolderConfig_path, yaml_file)
            with open(config_file_path, 'r') as file:
                config = yaml_safe_load(file)
                if config['current']:
                    return config_file_path
        return None

    def check_devices_load_comboboxes_load_config_file(self):
        """SK: Funkcia ktorá nám načíta comboboxi a class 'my_settings' pre daný typ senzora
        EN: A function that loads comboboxes and class 'my_settings' for a given type of sensor."""
        self.ui.sens_type_comboBox.blockSignals(True)
        self.ui.opt_config_combobox.blockSignals(True)

        self.ui.sens_type_comboBox.clear()

        # load optical sensor types
        self.ui.sens_type_comboBox.addItem('Accelerometer')
        self.ui.sens_type_comboBox.addItem('Strain')
        self.ui.sens_type_comboBox.addItem('Test')
        self.ui.sens_type_comboBox.setCurrentText(self.sens_type)

        if self.sens_type == "Accelerometer":
            self.my_settings = MySettings(self.starting_folder)
        elif self.sens_type == "Strain":
            self.my_settings = MySettings_strain(self.starting_folder)
        try:
            if self.thread_check_usb_devices is not None:
                self.thread_check_usb_devices.my_settings = self.my_settings
        except Exception:
            pass

        load_all_config_files(self.ui.opt_config_combobox, self.config_file_path, self.sens_type,
                              self.my_settings.subfolderConfig_path)

        if self.config_file_path is not None and os_path.exists(self.config_file_path):
            self.config_contains_none = self.my_settings.load_config_file(self.config_file_path)
        else:
            self.config_contains_none, self.config_file_path = self.my_settings.create_config_file()

        self.ui.sens_type_comboBox.blockSignals(False)
        self.ui.opt_config_combobox.blockSignals(False)

    def open_settings_window(self):
        """SK: Funckia ktorá nám otvorí okno s nastaveniami.
        EN: A function that opens a window with settings."""
        text = self.ui.sens_type_comboBox.currentText()
        self.thread_check_usb_devices.termination = True
        if text == "Accelerometer":
            self.settings_window = self.my_settings_window_acc(True, self, self.my_settings)
        elif text == "Strain":
            self.settings_window = self.my_settings_window_strain(True, self, self.my_settings)

        self.hide()

    def start_calib_app(self):
        """SK: Funckia ktorá na základne aký typ senzora zavolá funckiu na spustenie okna na
        kalibráciu daného typu senzora.
        EN: A function that, based on the type of sensor, calls a function to launch the calibration window for that
        specific type of sensor."""
        text = self.ui.sens_type_comboBox.currentText()
        if text == "Accelerometer":
            self.start_acc()
        elif text == "Strain":
            self.start_strain()

    def start_strain(self):
        """SK: Funckia ktorá nám spustí funkciu start_any() a po 100ms spustí funkciu na
        načítanie strain kalibračného okna.
        EN: A function that initiates the start_any() function and, after 100ms, launches the function for
        loading the strain calibration window."""
        self.start_any()
        QTimer.singleShot(100, self.start_strain_window)

    def start_acc(self):
        """SK: Funckia ktorá nám spustí funkciu start_any() a po 100ms spustí funkciu na načítanie acc kalibračného okna.
        EN: A function that initiates the start_any() function and, after 100ms, launches the function for loading the acc
        calibration window."""
        self.start_any()
        QTimer.singleShot(100, self.start_acc_window)

    def start_strain_window(self):
        """SK: Funkcia ktorá nám načíta strain okno na kalibráciu.
        EN: A function that loads the strain calibration window."""
        from SensStrain.MyMainWindow import MyMainWindow
        print("START STRAIN")
        self.calib_window = MyMainWindow(self, self.my_settings)
        self.calib_window.first_start(self.operator)
        self.ui.start_app.setText(self.translations[self.lang]["start_app_b"])

    def start_any(self):
        """SK: Funkcia ktorá nám vykoná všetky potrebné úkony pre úspešné spustenie kalibračného okna.
        EN: A function that performs all necessary actions for the successful launch of the calibration window."""
        self.save_sens_type()
        self.ui.start_app.setStyleSheet("QPushButton:hover { background-color: none; }")
        self.ui.start_app.setEnabled(False)
        self.ui.start_app.setText(self.translations[self.lang]["start_app_b"])
        self.ui.opt_config_combobox.setEnabled(False)
        self.ui.sens_type_comboBox.setEnabled(False)
        self.ui.open_settings_btn.setEnabled(False)
        self.ui.combobox_sel_operator.setEnabled(False)
        self.ui.btn_add_operator.setEnabled(False)
        self.ui.menubar.setEnabled(False)
        self.thread_check_usb_devices.termination = True

    def start_acc_window(self):
        """SK: Funkcia ktorá nám načíta acc okno na kalibráciu a spustí sentinel-D.
           EN: A function that loads the strain calibration window and starts sentinel-D."""
        from SensAcc.MyMainWindow import MyMainWindow
        path_config = os_path.join(self.my_settings.folder_sentinel_D_folder, "config.ini")
        config = ConfigParser()
        with codecs_open(path_config, 'r', encoding='utf-8-sig') as f:
            config.read_file(f)
        config.set('general', 'export_folder_path', self.my_settings.folder_opt_export)
        with open(path_config, 'w') as configfile:
            config.write(configfile)
        start_sentinel_d(self.my_settings.opt_project, self.my_settings.folder_sentinel_D_folder, self.my_settings.subfolder_sentinel_project)
        self.operator = self.ui.combobox_sel_operator.currentText()

        self.calib_window = MyMainWindow(self, self.my_settings)
        self.calib_window.first_sentinel_start(self.operator)
        self.check_last_calib()
        self.ui.start_app.setText(self.translations[self.lang]["start_app_b"])

    def show_back(self):
        """SK: Funckia ktorá nám vykonáva zmeny pozície a veľkosti okna pred tým ako sa zavolá show() funkcia,
        vykoná prvé spustenie vlákna na kontrolu priojenia zariadení.
        EN: A function that performs changes to the position and size of the window before the show() function is called,
        and executes the first run of the thread for checking device connections."""
        from ThreadCheckDevicesConnected import ThreadCheckDevicesConnected
        self.set_language()
        if self.thread_check_usb_devices is None or not self.thread_check_usb_devices.isRunning():
            self.thread_check_usb_devices = ThreadCheckDevicesConnected(self.my_settings, self)
            self.thread_check_usb_devices.all_connected.connect(self.all_dev_connected_signal)
            self.thread_check_usb_devices.all_connected_strain.connect(self.all_dev_connected_signal_strain)
            self.thread_check_usb_devices.start()

        self.setFixedSize(int(self.width()*self.window_scale_delta),
                          int(self.height()*self.window_scale_delta))
        scale_app(self, self.window_scale_delta)
        self.window_scale_delta = 1
        self.check_devices_load_comboboxes_load_config_file()
        if self.operator:
            self.load_operators(self.operator)
        else:
            self.load_operators()

        QTimer.singleShot(0, lambda: center_on_screen(self))

    def showEvent(self, a0):
        """SK: Override pre funkciu showEvent, načíta nám class ktorá nám drží nastavenia pre daný typ senzora.
        EN: Override for the showEvent function, loads a class that holds settings for a specific type of sensor."""
        from SensAcc.MySettingsWindow import MySettingsWindow as MySettingsWindowStrain
        from SensStrain.MySettingsWindow import MySettingsWindow as MySettingsWindowAcc
        if self.my_settings_window_acc is None:
            self.my_settings_window_acc = MySettingsWindowAcc
            self.my_settings_window_strain = MySettingsWindowStrain
            self.splash.hide()

    def closeEvent(self, event):
        """SK. Override pre funkciu closeEvent, vytvorí pop-up window ktorý sa spýta či naozaj chceme ukončiť aplikáciu,
        vykoná všetky potrebné ukony pre správne vypnutie aplikácie.
        EN: Override for the closeEvent function, creates a pop-up window that asks if we really want to close
        the application, performs all necessary actions for the proper shutdown of the application."""
        trans = self.translations
        lang = self.lang
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
            self.thread_check_usb_devices.termination = True
            self.thread_check_usb_devices.wait()
            event.accept()
        else:
            event.ignore()

    def set_language(self):
        """SK: Funkcia ktorá nám nastaví jazyk pre všetok text na konkrétnom okne.
        EN: A function that sets the language for all text in a specific window."""
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
        """SK: Funkcia ktorá nám načíta všeobecné/globálne nastavenia.
        EN: A function that loads general/global settings."""
        with open("global_settings.yaml", 'r') as file:
            config = yaml_safe_load(file)
        self.version = config["version"]
        self.lang = config["language"]
        self.window_scale = config["windows_scale"]
        self.last_ref_calib = config["last_ref_calib_acc"]
        self.calib_treshold = int(config["treshold"])
        self.sens_type = config['last_sens_type']

    def save_sens_type(self):
        """SK: Funkcia na uloženie posledne použitého typu senzora pri spustení konfiguračného súboru.
        EN: A function to save the last used type of sensor when launching the configuration file."""
        try:
            with open("global_settings.yaml", 'r') as file:
                config = yaml_safe_load(file)
            config['last_sens_type'] = self.sens_type
            with open("global_settings.yaml", 'w') as file:
                yaml_safe_dump(config, file)
        except Exception as e:
            print(f"An error occurred while saving sens_type: {e}")

    def check_last_calib(self, get_bool=False):
        """SK: Funkcia ktorá nám skontroluje poslednú kalibráciu referenčného senzora, otvorí pop-up.
        EN: A function that checks the last calibration of the reference sensor and opens a pop-up."""
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
