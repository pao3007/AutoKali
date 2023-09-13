import subprocess
from configparser import ConfigParser
from codecs import open as codecs_open

import psutil
from wmi import WMI as wmi_WMI
from PyQt5.QtCore import QThread, QFileInfo
# from scipy.fft import fft
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget
from os import (chdir as os_chdir, system as os_system, path as os_path, remove as os_remove, makedirs as os_makedirs,
                listdir as os_listdir, chmod as os_chmod)
from pyvisa import ResourceManager as pyvisa_ResourceManager, VisaIOError, constants
from DatabaseCom import DatabaseCom
from xml.etree.ElementTree import parse as ET_parse
from yaml import safe_load as yaml_safe_load
from re import search as re_search
from shutil import copy as shutil_copy
from platform import system as platform_system
from csv import writer as csv_writer


def center_on_screen(self):
    screen_geo = QApplication.desktop().screenGeometry()
    window_geo = self.geometry()

    # Calculate the horizontal and vertical center position
    center_x = int((screen_geo.width() - window_geo.width()) / 2)
    center_y = int((screen_geo.height() - window_geo.height()) / 2)

    # Move the window to the calculated position
    self.move(center_x, center_y)


def scale_app(widget, scale_factor: float):
    # Check if it's a QWidget instance before accessing specific attributes
    if isinstance(widget, QWidget):

        # Adjust font size
        if hasattr(widget, 'font') and hasattr(widget, 'setFont'):
            font = widget.font()
            font.setPointSize(int(font.pointSize() * scale_factor))
            widget.setFont(font)

        # Adjust size for all widgets
        current_size = widget.size()
        widget.resize(int(current_size.width() * scale_factor), int(current_size.height() * scale_factor))

        # Adjust position for all widgets
        current_pos = widget.pos()
        widget.move(int(current_pos.x() * scale_factor), int(current_pos.y() * scale_factor))

    # Recursively scale child widgets or objects
    for child in widget.children():
        scale_app(child, scale_factor)


def start_sentinel_d(project: str, sentinel_app_folder: str):  # ! vybrat path to .exe a project
    print(sentinel_app_folder)
    os_chdir(sentinel_app_folder)
    os_system("start /min ClientApp_Dyn " + project)


def start_sentinel_modbus(modbus_path: str, sentinel_path: str, project: str, opt_channels: int):
    sentinel_app = modbus_path
    os_chdir(sentinel_app)

    config = ConfigParser()
    with codecs_open('settings.ini', 'r', encoding='utf-8-sig') as f:
        config.read_file(f)

    if opt_channels == 1:
        config.set('ranges', 'definition_file', f'{sentinel_path}/Sensors/{project}')
    elif opt_channels == 2:
        config.set('ranges', 'definition_file', f'{sentinel_path}/Sensors/{project}')

    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

    os_system("start /min Sentinel-Dynamic-Modbus")


def kill_sentinel(dyn: bool, mod: bool):
    def kill_process(app_name):
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if app_name.lower() in process.info['name'].lower():
                psutil.Process(process.info['pid']).terminate()

    if dyn:
        app_name = "ClientApp_Dyn"
        kill_process(app_name)

    if mod:
        app_name = "Sentinel-Dynamic-Modbus"
        kill_process(app_name)


# def data_contains_sinus2(samples, sample_rate: int, peak_threshold: float):
#     # Perform Fast Fourier Transform
#     data = np.array(samples)
#     yf = fft(data)
#     xf = np.linspace(0.0, 1.0 / (2.0 / sample_rate), len(data) // 2)
#
#     # Check if the signal forms a periodic waveform
#     # If there is a peak in the frequency domain, we can say that there is a periodic signal
#     peak_freqs = xf[np.abs(yf[:len(data) // 2]) > peak_threshold]
#
#     return len(peak_freqs)


def dominant_frequency(samples, sampling_rate):
    # Calculate the FFT and its magnitude
    fft_values = np.fft.fft(samples)
    magnitudes = np.abs(fft_values)

    # Find the frequency with the highest magnitude
    dominant_freq_index = np.argmax(magnitudes[1:]) + 1  # exclude the 0Hz component

    # Calculate the actual frequency in Hz
    freqs = np.fft.fftfreq(len(samples), 1 / sampling_rate)
    dominant_freq = freqs[dominant_freq_index]

    return abs(dominant_freq)


def start_modbus(folder_sentinel_modbus_folder: str, folder_sentinel_d_folder: str, opt_project: str,
                 folder_opt_export: str, opt_channels: int, opt_sentinel_file_name: str):
    kill_sentinel(True, False)
    start_sentinel_modbus(folder_sentinel_modbus_folder, folder_sentinel_d_folder, opt_project, opt_channels)
    QThread.msleep(100)

    os_chdir(folder_opt_export)

    if os_path.exists(opt_sentinel_file_name + '.csv'):
        os_remove(opt_sentinel_file_name + '.csv')


def check_usb(opt_vendor_ids, ref_vendor_ids):
    c = wmi_WMI()
    opt = False
    ref = False
    for usb in c.Win32_USBControllerDevice():
        try:
            device = usb.Dependent
            # The string to parse is like 'USB\\VID_045E&PID_07A5&MI_02\\7&37207CFF&0&0002'
            # VID is the vendor id
            device = device.DeviceID
            vid_start = device.find('VID_') + 4
            vid_end = device.find('&', vid_start)
            v_id = device[vid_start:vid_end]

            if v_id.upper() in [str(id1) for id1 in opt_vendor_ids]:
                opt = True
            if v_id.upper() in [str(id1) for id1 in ref_vendor_ids]:
                ref = True
            if opt and ref:
                break
        except Exception as e:
            pass
            return False, False
    return opt, ref


def check_function_gen_connected(generator_id, first_start=False):
    rm = pyvisa_ResourceManager()
    devices = rm.list_resources()
    # print(devices)

    if generator_id in devices:
        if first_start:
            try:
                rm.open_resource(generator_id)
                rm.close()
                return True, False
            except Exception as e:
                print(e)
                return True, True
        return True, False
    return False, False


def load_all_config_files(combobox, config_file_path: str, opt_sensor_type: str, subfolderConfig_path: str):
    combobox.blockSignals(True)
    combobox.clear()
    yaml_files = return_all_configs(opt_sensor_type, subfolderConfig_path)
    for yaml_file in yaml_files:
        combobox.addItem(os_path.basename(yaml_file))
    if config_file_path is not None:
        combobox.setCurrentText(QFileInfo(config_file_path).fileName())
    combobox.blockSignals(False)
    return yaml_files


def set_wavelengths(s_n: str, sentinel_file_path: str, project: str):
    iwl = DatabaseCom()
    wl = iwl.load_sylex_nominal_wavelength(objednavka_id=s_n)

    project_path = os_path.join(sentinel_file_path, f"Sensors/{project}")

    if len(wl) == 2:
        mid = np.abs(wl[0]-wl[1])/2

        tree = ET_parse(project_path)
        root = tree.getroot()

        i = 0
        for peak_range in root.findall(".//PeakRangeDefinition"):
            # print("PEAK")
            # Find RangeStart and RangeEnd elements
            range_start = peak_range.find("RangeStart")
            range_end = peak_range.find("RangeEnd")

            if range_start is not None and range_end is not None and i < len(wl):
                # print("Change")
                # Modify their values
                if i == 0:
                    range_start.text = str(float(wl[i] - 10))
                    range_end.text = str(float(wl[i] + mid))
                else:
                    range_start.text = str(float(wl[i] - mid))
                    range_end.text = str(float(wl[i] + 10))
                i += 1
            else:
                return -2
        tree.write(project_path)
    return wl


def get_params(s_n):
    iwl = DatabaseCom()
    info = iwl.load_sylex_nominal_wavelength(objednavka_id=re_search(r'(-?\d+(\.\d+)?)', s_n).group(1), all_info=True)
    arr = [str(info[0]), str(info[5])]
    arr.extend([str(info[3]), str(info[6])])
    return arr


def return_all_configs(opt_sensor_type: str, subfolder_config_path: str):
    from glob import glob
    yaml_files = glob(os_path.join(subfolder_config_path, '*.yaml'))
    yaml_return = []
    for yaml_file in yaml_files:
        config_file_path = os_path.join(subfolder_config_path, yaml_file)
        with open(config_file_path, 'r') as file:
            config = yaml_safe_load(file)
            if config['opt_measurement']['sensor_type'] == opt_sensor_type:
                yaml_return.append(yaml_file)
    return yaml_return


def copy_files(serial_number, folder_id, source_folders, export_folder):
    try:
        return_str = []
        # Define folder names to associate with folder types
        folder_name_dict = {'optical': 'opt', 'reference': 'ref', 'calibration': 'cal'}

        # Find folder by ID and company name
        target_folder = None
        for folder in os_listdir(export_folder):
            if folder.startswith(f"{folder_id}_"):
                target_folder = os_path.join(export_folder, folder)
                break

        if target_folder is None:
            print(f"No folder with ID {folder_id} found in {export_folder}")
            return

        # Inside target folder, find or create folder ID_kalibracia
        kalibracia_folder = os_path.join(target_folder, f"{folder_id}_kalibracia")
        if not os_path.exists(kalibracia_folder):
            os_makedirs(kalibracia_folder)

        # Check for existence or create new subfolders (opt, ref, cal)
        for short_name in folder_name_dict.values():
            sub_folder = os_path.join(kalibracia_folder, short_name)
            if not os_path.exists(sub_folder):
                os_makedirs(sub_folder)

        # Loop through source folders to find the file based on the serial number
        for folder_type, folder_path in source_folders.items():
            file_found = False  # Initialize a flag for found files
            for file_name in os_listdir(folder_path):
                # Verify the file is a CSV file
                if not file_name.endswith('.csv'):
                    continue

                name_without_extension = os_path.splitext(file_name)[0]  # Strip the file extension

                if name_without_extension == serial_number:
                    file_found = True  # Update the flag
                    source_file = os_path.join(folder_path, file_name)

                    target_subfolder = os_path.join(kalibracia_folder, folder_name_dict[folder_type])
                    target_file = os_path.join(target_subfolder, file_name)

                    shutil_copy(source_file, target_file)

            if not file_found:
                return_str.append(f"No file with serial number {serial_number} found in {folder_path}")

        if len(return_str) == 0:
            return_str = (0, "Export to the local raw database was successful!")
        else:
            return_str = (-1, return_str)
    except Exception as e:
        return -1, f"Unexpected error happened during export to the local raw DB: \n {e}"
    return return_str


def set_read_only(file_path):
    if platform_system() == "Windows":
        os_system(f"attrib +r {file_path}")
    else:
        os_chmod(file_path, 0o444)


def set_read_write(file_path):
    if platform_system() == "Windows":
        os_system(f"attrib -r {file_path}")
    else:
        os_chmod(file_path, 0o666)


def disable_ui_elements(ui_elements):
    for element in ui_elements:
        element.setEnabled(False)


def enable_ui_elements(ui_elements):
    for element in ui_elements:
        element.setEnabled(True)


def save_statistics_to_csv(folder_path, file_name, time_stamp, serial_number, sensitivity, wl1, wl2=None):
    try:
        date = time_stamp.split(" ")[0]
        wavelengths = str(wl1)
        if wl2 is not None:
            wavelengths += "/" + str(wl2)

        # Append .csv to the file name
        file_name += ".csv"

        # Check if folder exists, if not, create it
        stats_folder_path = os_path.join(folder_path, "statistics")
        if not os_path.exists(stats_folder_path):
            os_makedirs(stats_folder_path)

        # Check if file exists, if not, create it and write header
        file_path = os_path.join(stats_folder_path, file_name)
        file_exists = os_path.exists(file_path)

        with open(file_path, mode='a', newline='') as file:
            writer = csv_writer(file)

            if not file_exists:
                writer.writerow(['Date', 'Serial Number', 'Wavelengths', 'Sensitivity'])

            writer.writerow([date, serial_number, wavelengths, str(sensitivity)])
        return 0
    except Exception as e:
        return e
