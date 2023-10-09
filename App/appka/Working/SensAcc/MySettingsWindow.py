from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from yaml import safe_dump as yaml_dump, safe_load as yaml_safe_load
from nidaqmx import system as nidaqmx_system
from os import path as os_path, chdir as os_chdir
from MyStartUpWindow import MyStartUpWindow
from definitions import center_on_screen, scale_app, load_all_config_files, enable_ui_elements
from pyvisa import ResourceManager as pyvisa_ResourceManager
from SensAcc.SettingsParams import MySettings
from subprocess import run as subprocess_run
from json import load as json_load


def set_style_sheet_btn_clicked(btn, font_size, right_border):
    btn.setStyleSheet("border: 2px solid gray;border-color:rgb(208,208,208);border-bottom-color: rgb(60, 60, 60); "
                      "border-radius: 8px;font: 700 " + font_size +
                      " \"Segoe UI\";padding: 0 8px;background: rgb(60, 60, 60);"
                      "color: rgb(208,208,208);" + right_border)


def set_style_sheet_btn_unclicked(btn, font_size):
    btn.setStyleSheet("border: 2px solid gray;border-color:rgb(208,208,208);border-radius: 8px;font: 600 " +
                      font_size + "\"Segoe UI\";padding: 0 8px;"
                                  "background: rgb(60, 60, 60);color: rgb(208,208,208);")


def slider_scale_get_real_value(value):
    def get_key_for_value(d, key_value):
        for k, v in d.items():
            if v == key_value:
                return k
        return None

    # Mapping integer values of the slider to the desired float values
    mapping = {
        1: 1,
        2: 1.25,
        3: 1.5,
        4: 1.75,
        5: 2
    }
    return mapping[int(value)], get_key_for_value(mapping, value)


class MySettingsWindow(QMainWindow):
    def __init__(self, start, window: MyStartUpWindow, my_settings: MySettings):
        super().__init__()
        self.logged_in = False
        from SensAcc.ThreadSettingsCheckNew import ThreadSettingsCheckNew
        self.my_settings = my_settings
        self.all_configs = None
        self.resources = None
        self.my_starting_window = window
        self.slider_value = self.my_starting_window.window_scale
        from gui.settings import Ui_Settings
        self.config_file_path = None
        self.nidaq_devices = None
        self.start = start
        self.ui = Ui_Settings()
        self.ui.setupUi(self)
        self.load_settings()
        self.config_file = None
        self.local_lang = None

        # btns
        self.ui.save_btn.clicked.connect(self.save_settings)
        self.ui.cancel_btn.clicked.connect(self.load_settings)
        self.ui.close_btn.clicked.connect(self.close)
        self.ui.login_btn.clicked.connect(self.login_into_settings)

        self.ui.main_folder_btn.clicked.connect(self.main_folder_path_select)
        self.ui.ref_exp_fold_btn.clicked.connect(self.ref_export_folder_path_select)
        self.ui.ref_export_fold_raw_btn.clicked.connect(self.ref_export_raw_folder_path_select)

        self.ui.combo_box_lang.currentTextChanged.connect(self.lang_changed)

        self.ui.opt_exp_fold_btn.clicked.connect(self.opt_export_folder_path_select)
        self.ui.opt_exp_fold_raw_btn.clicked.connect(self.opt_export_raw_folder_path_select)
        self.ui.opt_loaded_project_btn.clicked.connect(self.opt_sentinel_load_proj)
        self.ui.calib_databse_export_btn.clicked.connect(self.calib_local_db_export_folder_path_select)
        self.ui.calib_statistics_btn.clicked.connect(self.stats_btn_clicked)
        self.ui.db_btn.clicked.connect(self.open_db_yaml)
        self.ui.vendors_btn.clicked.connect(self.open_vendor_yaml)

        self.ui.btn_ref_tab.clicked.connect(self.clicked_btn_reference)
        self.ui.btn_opt_tab.clicked.connect(self.clicked_btn_optical)
        self.ui.btn_calib_tab.clicked.connect(self.clicked_btn_calib)
        self.ui.btn_gen_tab.clicked.connect(self.clicked_btn_gen)
        self.ui.btn_db_others_tab.clicked.connect(self.clicked_btn_db_others)
        self.ui.btn_ref_calib_done.clicked.connect(self.ref_calib_done_clicked)

        self.ui.slider_win_scale.setRange(1, 5)
        self.ui.slider_win_scale.valueChanged.connect(self.slider_scale_changed)
        path = os_path.join(self.my_settings.starting_folder, "images/logo.png")
        self.ui.logo_label.setPixmap(QPixmap(path))

        self.ui.calib_export_btn.clicked.connect(self.calib_export_folder_path_select)
        self.ui.save_as_btn.clicked.connect(self.save_as_settings)
        self.ui.select_config_file.currentTextChanged.connect(self.select_config_file_combobox_changed)
        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_gen.hide()
        self.ui.widget_db_others.hide()

        self.btn_translate_dy = 8
        self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(), self.ui.btn_ref_tab.pos().y() + self.btn_translate_dy)
        self.ui.btn_ref_tab.setEnabled(False)
        self.thread_check_new = ThreadSettingsCheckNew(self.nidaq_devices, self.resources, self.all_configs,
                                                       self.my_settings)
        self.thread_check_new.status.connect(self.new_setting_enabled)
        self.thread_check_new.start()
        path = os_path.join(self.my_settings.starting_folder, "images/logo_icon.png")
        self.setWindowIcon(QIcon(path))
        self.setFixedSize(self.width(), int(self.height()*0.96))
        if self.my_starting_window.check_last_calib(get_bool=True):
            self.ui.label_recalib.setText(f"<span style='color:red;'>{self.my_starting_window.translations[self.my_starting_window.lang]['label_recalib_old']}{str(self.my_starting_window.last_ref_calib)}</span>")
        else:
            self.ui.label_recalib.setText(
                f"{self.my_starting_window.translations[self.my_starting_window.lang]['label_recalib_ok']}{str(self.my_starting_window.last_ref_calib)}")
        self.show_back()

    def lang_changed(self, text):
        self.set_language(lang=text)
        self.local_lang = text

    def open_file_using_notepad(self, yaml_file_path):
        if os_path.exists(yaml_file_path):
            # Open the .yaml file using Windows Notepad
            subprocess_run(["notepad.exe", yaml_file_path])
        else:
            print(f"File {yaml_file_path} does not exist.")

    def open_vendor_yaml(self):
        yaml_file_path = self.my_starting_window.yaml_devices_vendor
        self.open_file_using_notepad(yaml_file_path)

    def open_db_yaml(self):
        yaml_file_path = self.my_starting_window.yaml_database_com
        self.open_file_using_notepad(yaml_file_path)

    def login_into_settings(self):
        pswd_dialog = QDialog(self)
        layout = QVBoxLayout()
        lang = self.local_lang if self.local_lang is not None else self.my_starting_window.lang

        password_label = QLabel(self.my_starting_window.translations[lang]["password_label"])
        password_label.setStyleSheet("color: rgb(208, 208, 208);")
        layout.addWidget(password_label)

        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setStyleSheet("color: rgb(208, 208, 208);")
        layout.addWidget(password_input)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(pswd_dialog.accept)
        ok_button.setStyleSheet("border: 1px solid gray; border-color:rgb(208,208,208); border-radius: 3px; color: "
                                "rgb(208, 208, 208); background-color: rgb(44, 44, 44);")
        layout.addWidget(ok_button)

        pswd_dialog.setLayout(layout)
        result = pswd_dialog.exec_()

        if result == QDialog.Accepted:
            password = password_input.text()
            if password == "sealseal":
                enable_ui_elements(self.make_list_of_elements_to_enable())
                enable_ui_elements(self.make_list_of_elements_to_enable())
                self.ui.label_login_warning.setText(self.my_starting_window.translations[lang]["label_login_warning_ok"])
                self.ui.login_btn.setEnabled(False)
                self.logged_in = True
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(self.my_starting_window.translations[lang]["bad_psd"])
                msg.setWindowTitle("Error")
                msg.exec_()

    def slider_scale_changed(self, value):
        self.slider_value, _ = slider_scale_get_real_value(value)
        self.ui.settings_scale2x_label.setText(str(self.slider_value) + "x")

    def move_btns_back(self):
        if not self.ui.btn_calib_tab.isEnabled():
            self.ui.btn_calib_tab.move(self.ui.btn_calib_tab.pos().x(),
                                       self.ui.btn_calib_tab.pos().y() - self.btn_translate_dy)
            set_style_sheet_btn_unclicked(self.ui.btn_calib_tab, "8pt")

        if not self.ui.btn_gen_tab.isEnabled():
            self.ui.btn_gen_tab.move(self.ui.btn_gen_tab.pos().x(),
                                     self.ui.btn_gen_tab.pos().y() - self.btn_translate_dy)
            set_style_sheet_btn_unclicked(self.ui.btn_gen_tab, "8pt")

        if not self.ui.btn_opt_tab.isEnabled():
            self.ui.btn_opt_tab.move(self.ui.btn_opt_tab.pos().x(),
                                     self.ui.btn_opt_tab.pos().y() - self.btn_translate_dy)
            set_style_sheet_btn_unclicked(self.ui.btn_opt_tab, "10pt")

        if not self.ui.btn_ref_tab.isEnabled():
            self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(),
                                     self.ui.btn_ref_tab.pos().y() - self.btn_translate_dy)
            set_style_sheet_btn_unclicked(self.ui.btn_ref_tab, "10pt")

        if not self.ui.btn_db_others_tab.isEnabled():
            self.ui.btn_db_others_tab.move(self.ui.btn_db_others_tab.pos().x(),
                                     self.ui.btn_db_others_tab.pos().y() - self.btn_translate_dy)
            set_style_sheet_btn_unclicked(self.ui.btn_db_others_tab, "10pt")

    def clicked_btn_reference(self):
        self.move_btns_back()

        self.ui.btn_ref_tab.move(self.ui.btn_ref_tab.pos().x(), self.ui.btn_ref_tab.pos().y() + self.btn_translate_dy)
        set_style_sheet_btn_clicked(self.ui.btn_ref_tab, "10pt", "border-right-color: rgb(60, 60, 60)")

        self.ui.btn_ref_tab.setEnabled(False)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)
        self.ui.btn_db_others_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.show()
        self.ui.widget_gen.hide()
        self.ui.widget_db_others.hide()

    def clicked_btn_optical(self):
        self.move_btns_back()

        self.ui.btn_opt_tab.move(self.ui.btn_opt_tab.pos().x(), self.ui.btn_opt_tab.pos().y() + self.btn_translate_dy)
        set_style_sheet_btn_clicked(self.ui.btn_opt_tab, "10pt", "border-right-color: rgb(60, 60, 60);")

        self.ui.btn_opt_tab.setEnabled(False)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)
        self.ui.btn_db_others_tab.setEnabled(True)

        self.ui.widget_opt.show()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.hide()
        self.ui.widget_db_others.hide()

    def clicked_btn_calib(self):
        self.move_btns_back()

        self.ui.btn_calib_tab.move(self.ui.btn_calib_tab.pos().x(),
                                   self.ui.btn_calib_tab.pos().y() + self.btn_translate_dy)
        set_style_sheet_btn_clicked(self.ui.btn_calib_tab, "8pt", "border-right-color: rgb(60, 60, 60);")

        self.ui.btn_calib_tab.setEnabled(False)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)
        self.ui.btn_db_others_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.show()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.hide()
        self.ui.widget_db_others.hide()

    def clicked_btn_gen(self):
        self.move_btns_back()

        self.ui.btn_gen_tab.move(self.ui.btn_gen_tab.pos().x(), self.ui.btn_gen_tab.pos().y() + self.btn_translate_dy)
        set_style_sheet_btn_clicked(self.ui.btn_gen_tab, "8pt", "border-right-color: rgb(60, 60, 60);")

        self.ui.btn_gen_tab.setEnabled(False)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_db_others_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.show()
        self.ui.widget_db_others.hide()

    def clicked_btn_db_others(self):
        self.move_btns_back()

        self.ui.btn_db_others_tab.move(self.ui.btn_db_others_tab.pos().x(), self.ui.btn_db_others_tab.pos().y() + self.btn_translate_dy)
        set_style_sheet_btn_clicked(self.ui.btn_db_others_tab, "8pt", "")

        self.ui.btn_db_others_tab.setEnabled(False)
        self.ui.btn_calib_tab.setEnabled(True)
        self.ui.btn_ref_tab.setEnabled(True)
        self.ui.btn_opt_tab.setEnabled(True)
        self.ui.btn_gen_tab.setEnabled(True)

        self.ui.widget_opt.hide()
        self.ui.widget_calib.hide()
        self.ui.widget_ref.hide()
        self.ui.widget_gen.hide()
        self.ui.widget_db_others.show()

    def save_as_settings(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save YAML File", self.my_settings.subfolderConfig_path,
                                                   "YAML Files (*.yaml);;All Files (*)",
                                                   options=options)
        print(file_path)
        if file_path:
            self.my_starting_window.current_conf = False
            self.my_starting_window.none = self.my_settings.save_config_file(False, self.my_starting_window.config_file_path)
            with open(file_path, 'w') as file:
                yaml_dump(self.my_settings.default_config(self.my_settings.opt_sensor_type), file)
            with open(file_path, 'r') as file:
                self.my_starting_window.config = yaml_safe_load(file)
            self.my_starting_window.current_conf = True
            self.my_starting_window.config_file_path = file_path
            self.save_settings()

    def save_settings(self):
        self.my_starting_window.window_scale_delta = self.slider_value / self.my_starting_window.window_scale
        print(
            "VALUE : " + str(self.slider_value) + "/" + str(self.my_starting_window.window_scale) + "=" +
            str(self.my_starting_window.window_scale_delta))
        self.my_starting_window.window_scale = self.slider_value

        self.my_settings.ref_channel = self.ui.ref_channel_comboBox.currentText()
        self.my_settings.ref_device_name = self.ui.ref_device_comboBox.currentText()
        self.my_settings.calib_filter_data = self.ui.calib_filter_data_comboBox.currentText()

        self.my_settings.ref_sample_rate = int(self.ui.ref_sampling_rate_line.text())
        self.my_settings.opt_sampling_rate = int(self.ui.opt_sampling_rate_line.text())
        self.my_settings.opt_project = self.ui.opt_loaded_project_line.text()
        self.my_settings.opt_channels = int(self.ui.opt_channels_combobox.currentText())
        self.my_settings.calib_gain_mark = int(self.ui.calib_gain_mark_line.text())
        self.my_settings.calib_optical_sensitivity = float(self.ui.calib_opt_sensitivity_line.text())
        self.my_settings.calib_optical_sens_tolerance = float(self.ui.calib_opt_sensitivity_toler_line.text())
        self.my_settings.folder_main = self.ui.main_folder_line.text()
        self.my_settings.folder_ref_export = self.ui.ref_exp_folder_line.text()
        self.my_settings.folder_ref_export_raw = self.ui.ref_exp_folder_raw_line.text()
        self.my_settings.folder_opt_export = self.ui.opt_exp_folder_line.text()
        self.my_settings.folder_opt_export_raw = self.ui.opt_exp_folder_raw_line.text()
        self.my_settings.folder_calibration_export = self.ui.calib_export_folder_line.text()
        self.my_settings.folder_db_export_folder = self.ui.calib_database_export_folder_line.text()
        self.my_settings.calib_reference_sensitivity = float(self.ui.calib_ref_sensitivity_line.text())
        self.my_settings.calib_l_flatness = int(self.ui.calib_flatness_left_line.text())
        self.my_settings.calib_r_flatness = int(self.ui.calib_flatness_right_line.text())
        self.my_settings.calib_angle_set_freq = int(self.ui.calib_agnelsetfreq_line.text())
        self.my_settings.calib_phase_mark = int(self.ui.calib_phase_mark_line.text())
        self.my_settings.folder_statistics = self.ui.calib_statistics_folder_line.text()
        self.my_settings.auto_export = self.ui.check_auto_export.isChecked()
        self.my_settings.export_local_server = self.ui.check_export_to_loc_server.isChecked()

        self.my_settings.calib_plot = self.ui.calib_plot_graphs_check.isChecked()
        self.my_settings.calib_downsample = int(self.ui.calib_downsample_check.isChecked())
        self.my_settings.calib_do_spectrum = int(self.ui.calib_do_spectrum_check.isChecked())
        self.my_settings.slope_check = float(self.ui.calib_opt_slope_line.text())

        self.my_settings.generator_id = self.ui.gen_id_combobox.currentText()
        self.my_settings.generator_sweep_time = int(self.ui.gen_sweep_time_line.text())
        self.my_settings.generator_sweep_start_freq = int(self.ui.gen_start_freq_line.text())
        self.my_settings.generator_sweep_stop_freq = int(self.ui.gen_stop_freq_line.text())
        self.my_settings.generator_sweep_type = self.ui.gen_sweep_type_combobox.currentText()
        self.my_settings.generator_max_mvpp = int(self.ui.gen_vpp_line.text())

        self.my_settings.ref_measure_time = int(self.my_settings.generator_sweep_time + 3)
        self.my_settings.ref_number_of_samples = int(
            self.my_settings.ref_measure_time * self.my_settings.ref_sample_rate)

        self.my_starting_window.config_contains_none = self.my_settings.save_config_file(True, self.my_starting_window.config_file_path)
        self.my_starting_window.lang = self.ui.combo_box_lang.currentText()
        self.save_global_settings()

        self.close()

    def new_setting_enabled(self):
        self.load_settings()
        self.thread_check_new.nidaq_devices = self.nidaq_devices
        self.thread_check_new.all_configs = self.all_configs
        self.thread_check_new.resource = self.resources

    def load_settings(self):
        # load lineEdits
        _, value = slider_scale_get_real_value(self.my_starting_window.window_scale)
        self.ui.slider_win_scale.setValue(value)
        self.ui.settings_scale2x_label.setText(str(self.my_starting_window.window_scale) + "x")

        self.ui.main_folder_line.setText(self.my_settings.folder_main)
        self.ui.ref_sampling_rate_line.setText(str(self.my_settings.ref_sample_rate))
        self.ui.ref_exp_folder_line.setText(self.my_settings.folder_ref_export)
        self.ui.ref_exp_folder_raw_line.setText(self.my_settings.folder_ref_export_raw)
        self.ui.opt_sampling_rate_line.setText(str(self.my_settings.opt_sampling_rate))
        self.ui.opt_exp_folder_line.setText(self.my_settings.folder_opt_export)
        self.ui.opt_exp_folder_raw_line.setText(self.my_settings.folder_opt_export_raw)
        self.ui.opt_loaded_project_line.setText(self.my_settings.opt_project)
        self.ui.opt_channels_combobox.setCurrentText(str(self.my_settings.opt_channels))
        self.ui.calib_gain_mark_line.setText(str(self.my_settings.calib_gain_mark))
        self.ui.calib_opt_sensitivity_line.setText(str(self.my_settings.calib_optical_sensitivity))
        self.ui.calib_opt_sensitivity_toler_line.setText(str(self.my_settings.calib_optical_sens_tolerance))
        self.ui.calib_export_folder_line.setText(self.my_settings.folder_calibration_export)
        self.ui.calib_ref_sensitivity_line.setText(str(self.my_settings.calib_reference_sensitivity))
        self.ui.calib_flatness_left_line.setText(str(self.my_settings.calib_l_flatness))
        self.ui.calib_flatness_right_line.setText(str(self.my_settings.calib_r_flatness))
        self.ui.calib_phase_mark_line.setText(str(self.my_settings.calib_phase_mark))
        self.ui.calib_agnelsetfreq_line.setText(str(self.my_settings.calib_angle_set_freq))
        self.ui.calib_database_export_folder_line.setText(str(self.my_settings.folder_db_export_folder))
        self.ui.calib_statistics_folder_line.setText(str(self.my_settings.folder_statistics))
        self.ui.check_export_to_loc_server.setChecked(self.my_settings.export_local_server)
        self.ui.check_auto_export.setChecked(self.my_settings.auto_export)
        self.ui.gen_vpp_line.setText(str(self.my_settings.generator_max_mvpp))
        self.ui.gen_sweep_type_combobox.setCurrentText(str(self.my_settings.generator_sweep_type))
        self.ui.gen_stop_freq_line.setText(str(self.my_settings.generator_sweep_stop_freq))
        self.ui.gen_start_freq_line.setText(str(self.my_settings.generator_sweep_start_freq))
        self.ui.gen_sweep_time_line.setText(str(self.my_settings.generator_sweep_time))
        self.ui.calib_opt_slope_line.setText(str(self.my_settings.slope_check))
        # load checks
        self.ui.calib_downsample_check.setChecked(self.my_settings.calib_downsample)
        self.ui.calib_do_spectrum_check.setChecked(self.my_settings.calib_do_spectrum)
        self.ui.calib_plot_graphs_check.setChecked(self.my_settings.calib_plot)
        # load comboBox
        # devices
        self.ui.ref_device_comboBox.blockSignals(True)
        self.ui.ref_device_comboBox.clear()
        system = nidaqmx_system.System.local()
        self.nidaq_devices = system.devices.device_names
        for device in self.nidaq_devices:
            self.ui.ref_device_comboBox.addItem(f'{device}')
        if self.my_settings.ref_device_name is not None:
            self.ui.ref_device_comboBox.setCurrentText(self.my_settings.ref_device_name)
        # channels
        self.ui.ref_channel_comboBox.blockSignals(True)
        self.ui.ref_channel_comboBox.clear()
        self.ui.ref_channel_comboBox.addItem('ai0')
        self.ui.ref_channel_comboBox.addItem('ai1')
        self.ui.ref_channel_comboBox.addItem('ai2')
        if self.my_settings.ref_channel is not None:
            self.ui.ref_channel_comboBox.setCurrentText(self.my_settings.ref_channel)
        # gen device ID
        self.ui.gen_id_combobox.clear()
        self.gen_id_combobox_clicked()
        self.ui.gen_id_combobox.setCurrentText(str(self.my_settings.generator_id))
        # filter
        self.ui.calib_filter_data_comboBox.setCurrentText(self.my_settings.calib_filter_data)
        # configs
        self.all_configs = load_all_config_files(self.ui.select_config_file, self.my_starting_window.config_file_path,
                                                 self.my_settings.opt_sensor_type, self.my_settings.subfolderConfig_path)
        self.ui.ref_channel_comboBox.blockSignals(False)
        self.ui.ref_device_comboBox.blockSignals(False)
        self.ui.combo_box_lang.addItem("sk")
        self.ui.combo_box_lang.addItem("en")
        self.ui.combo_box_lang.setCurrentText(self.my_starting_window.lang)

    def gen_id_combobox_clicked(self):
        self.ui.gen_id_combobox.blockSignals(True)
        self.ui.gen_id_combobox.clear()
        self.ui.gen_id_combobox.addItem("SELECT DEVICE")
        i = 1
        rm = pyvisa_ResourceManager(r"C:\Windows\System32\visa64.dll")
        self.resources = rm.list_resources()
        for resource_name in self.resources:
            try:
                # instrument = rm.open_resource(resource_name)
                # instrument.close()
                self.ui.gen_id_combobox.addItem(str(resource_name))
                i += 1
            except Exception as e:
                print(self.resources)
                print(f"Error with {resource_name}: {e}")

        self.ui.gen_id_combobox.blockSignals(False)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        return folder_path

    def opt_sentinel_load_proj(self):

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Project",
                                                   directory=self.my_settings.subfolder_sentinel_project)

        if file_path:
            self.ui.opt_loaded_project_line.setText(os_path.basename(file_path))

    def select_config_file_combobox_changed(self, text):
        self.my_starting_window.current_conf = False
        self.my_starting_window.none = self.my_settings.save_config_file(False, self.my_starting_window.config_file_path)

        self.config_file = text
        self.config_file_path = os_path.join(self.my_settings.subfolderConfig_path, self.config_file)
        self.my_starting_window.config_file_path = self.config_file_path
        self.my_starting_window.none = self.my_settings.load_config_file(self.my_starting_window.config_file_path)

        self.my_starting_window.current_conf = True
        self.my_starting_window.none = self.my_settings.save_config_file(True, self.my_starting_window.config_file_path)

        self.load_settings()

    def calib_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.calib_export_folder_line.setText(folder_path)

    def calib_local_db_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.calib_database_export_folder_line.setText(folder_path)

    def stats_btn_clicked(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.calib_statistics_folder_line.setText(folder_path)

    def opt_export_raw_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.opt_exp_folder_raw_line.setText(folder_path)

    def opt_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.opt_exp_folder_line.setText(folder_path)

    def ref_export_raw_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.ref_exp_folder_raw_line.setText(folder_path)

    def ref_export_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.ref_exp_folder_line.setText(folder_path)

    def main_folder_path_select(self):
        folder_path = self.select_folder()
        if folder_path:
            self.ui.main_folder_line.setText(folder_path)

    def make_list_of_elements_to_enable(self):
        list_enable = [self.ui.calib_ref_sensitivity_line,
                       self.ui.ref_sampling_rate_line,
                       self.ui.ref_exp_folder_line,
                       self.ui.ref_exp_fold_btn,
                       self.ui.ref_exp_folder_raw_line,
                       self.ui.ref_export_fold_raw_btn,
                       self.ui.opt_channels_combobox,
                       self.ui.opt_sampling_rate_line,
                       self.ui.calib_opt_sensitivity_line,
                       self.ui.calib_opt_sensitivity_toler_line,
                       self.ui.opt_exp_folder_line,
                       self.ui.opt_exp_fold_btn,
                       self.ui.opt_exp_folder_raw_line,
                       self.ui.opt_exp_fold_raw_btn,
                       self.ui.opt_loaded_project_line,
                       self.ui.opt_loaded_project_btn,
                       self.ui.gen_sweep_type_combobox,
                       self.ui.gen_start_freq_line,
                       self.ui.gen_stop_freq_line,
                       self.ui.gen_sweep_time_line,
                       self.ui.gen_vpp_line,
                       self.ui.default_btn,
                       self.ui.db_btn,
                       self.ui.vendors_btn,
                       self.ui.main_folder_line,
                       self.ui.main_folder_btn,
                       self.ui.calib_gain_mark_line,
                       self.ui.calib_phase_mark_line,
                       self.ui.calib_filter_data_comboBox,
                       self.ui.calib_flatness_left_line,
                       self.ui.calib_agnelsetfreq_line,
                       self.ui.calib_export_folder_line,
                       self.ui.calib_export_btn,
                       self.ui.calib_database_export_folder_line,
                       self.ui.calib_databse_export_btn,
                       self.ui.calib_downsample_check,
                       self.ui.calib_do_spectrum_check,
                       self.ui.calib_plot_graphs_check,
                       self.ui.calib_flatness_right_line,
                       self.ui.calib_statistics_btn,
                       self.ui.calib_statistics_folder_line,
                       self.ui.btn_ref_calib_done,
                       self.ui.check_auto_export,
                       self.ui.check_export_to_loc_server,
                       self.ui.calib_opt_slope_line]
        return list_enable

    def show_back(self):
        self.set_language()
        self.setFixedSize(int(self.width()*self.my_starting_window.window_scale),
                          int(self.height()*self.my_starting_window.window_scale))
        scale_app(self, self.my_starting_window.window_scale)
        QTimer.singleShot(0, lambda: center_on_screen(self))

    def closeEvent(self, event):
        self.thread_check_new.terminate()
        if self.start:
            self.my_starting_window.show_back()
        else:
            self.my_starting_window.calib_window.show_back()
        super().closeEvent(event)

    def set_language(self, lang=None):
        if not lang:
            lang = self.my_starting_window.lang
        os_chdir(self.my_starting_window.starting_folder)
        file_path = "lang_pack.json"
        with open(file_path, 'r', encoding="utf-8") as f:
            trans = json_load(f)

            if self.my_starting_window.check_last_calib(get_bool=True):
                self.ui.label_recalib.setText(f"<span style='color:red;'>{trans[lang]['label_recalib_old']}{str(self.my_starting_window.last_ref_calib)}</span>")
            else:
                self.ui.label_recalib.setText(f"{trans[lang]['label_recalib_ok']}{str(self.my_starting_window.last_ref_calib)}")

        self.ui.settings_settings_label.setText(trans[lang]["settings_settings_label"])
        self.ui.btn_ref_calib_done.setText(trans[lang]["btn_ref_calib_done"])
        # self.ui.settings_plot_graph_lable.setText()
        # self.ui.settings_do_specrtum_label.setText()
        # self.ui.settings_gain_mark_label.setText()
        # self.ui.settings_filter_data_label.setText()
        # self.ui.setting_downsample_label.setText()
        # self.ui.settings_calib_flatness_label.setText()
        # self.ui.settings_calib_flatness_label_l.setText()
        # self.ui.settings_calib_flatness_label_r.setText()
        # self.ui.settings_calib_anglesetfreq_label.setText()
        # self.ui.settings_calib_phasemark_label.setText()
        # self.ui.settings_calib_export_label.setText()
        # self.ui.settings_exp_fold_opt_raw_label.setText()
        # self.ui.settings_opt_exp_fold_label.setText()
        # self.ui.settings_sampl_rate_opt_label.setText()
        # self.ui.settings_load_project_label.setText()
        # self.ui.settings_sentinel_fold_label.setText()
        # self.ui.settings_opt_channles_label.setText()
        # self.ui.settings_modbus_fold_label.setText()
        # self.ui.settings_opt_cal_sens_label.setText()
        # self.ui.settings_pm_g_label.setText()
        # self.ui.settings_opt_cal_sens_label_2.setText()
        # self.ui.setting_export_ref_folder_label.setText()
        # self.ui.settings_devie_label.setText()
        # self.ui.settings_channel_label.setText()
        # self.ui.setting_sampl_rate_ref_label.setText()
        # self.ui.settings_export_raw_label.setText()
        # self.ui.settings_ref_cal_sens_label.setText()
        # self.ui.settings_gen_id_label.setText()
        # self.ui.settings_gen_sweep_type_label.setText()
        # self.ui.settings_gen_sweep_freq_start_label.setText()
        # self.ui.settings_gen_sweep_freq_stop_label.setText()
        # self.ui.settings_gen_sweep_time_label.setText()
        # self.ui.settings_gen_vpp_label.setText()
        # self.ui.settings_s_label.setText()
        self.ui.settings_win_scale_label.setText(trans[lang]["settings_win_scale_label"])
        # self.ui.settings_main_folder_label.setText()
        # self.ui.settings_calib_export_label_2.setText()
        # self.ui.settings_calib_export_label_3.setText()
        self.ui.label_login_warning.setText(trans[lang]["label_login_warning" if not self.logged_in else "label_login_warning_ok"])
        self.ui.settings_lang_label.setText(trans[lang]["settings_lang_label"])

        self.ui.save_btn.setText(trans[lang]["save_btn"])
        self.ui.save_as_btn.setText(trans[lang]["save_as_btn"])
        self.ui.close_btn.setText(trans[lang]["close_btn"])
        self.ui.cancel_btn.setText(trans[lang]["cancel_btn"])
        self.ui.login_btn.setText(trans[lang]["login_btn" if not self.logged_in else "change_login_btn"])

    def ref_calib_done_clicked(self):
        from datetime import datetime
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        self.my_starting_window.last_ref_calib = current_date
        with open('global_settings.yaml', 'r') as f:
            config = yaml_safe_load(f)
            config["last_ref_calib"] = self.my_starting_window.last_ref_calib
        with open('global_settings.yaml', 'w') as f:
            yaml_dump(config, f)
        self.ui.label_recalib.setText(f"{self.my_starting_window.translations[self.my_starting_window.lang if self.local_lang is None else self.local_lang]['label_recalib_set']}{str(self.my_starting_window.last_ref_calib)}")

    def save_global_settings(self):
        with open('global_settings.yaml', 'r') as f:
            config = yaml_safe_load(f)
            config["language"] = self.my_starting_window.lang
            config["windows_scale"] = self.my_starting_window.window_scale

        with open('global_settings.yaml', 'w') as f:
            yaml_dump(config, f)


