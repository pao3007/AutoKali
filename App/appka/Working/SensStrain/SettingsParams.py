from yaml import safe_load as yaml_safe_load, dump as yaml_dump, YAMLError
from os import path as os_path, makedirs as os_makedirs


def check_file_path(file_path, default_path):
    if os_path.exists(file_path):
        return file_path
    else:
        return default_path


class MySettings:

    def __init__(self, starting_folder=None):
        print("INIT SETTINGS STRAIN")
        self.number_of_steps = 10
        self.max_stretch_unit = None
        self.max_stretch = None
        self.serial_no_motor_control = None
        self.stage_name = None
        self.stage_min_limit = 0
        self.stage_max_limit = None
        self.optical_sensor_mount_position = None
        self.polling_rate = 100

        self.slope_check = None
        self.folder_statistics = None
        self.folder_db_export_folder = None
        self.starting_folder = starting_folder
        self.config = None
        self.calib_optical_sens_tolerance = None

        self.opt_dev_vendor = None
        self.ref_dev_vendor = None
        self.opt_first_start = True
        self.check_usbs_first_start = True
        self.calib_window = None
        self.settings_window = None
        self.S_N = None
        self.auto_export = None
        self.export_local_server = None
        self.calib_plot = None
        self.pre_strain = None
        self.pre_strain_length = 0
        self.pre_strain_unit = "0"

        self.calib_optical_sensitivity = None
        self.opt_channels = None

        self.current_conf = None
        self.opt_sensor_type = "Strain"
        #
        documents_path = os_path.expanduser('~/Documents')
        #
        self.folder_main = os_path.join(documents_path, 'Sylex_sensors_export')
        self.folder_calibration_export = os_path.join(self.folder_main, 'calibration')
        config_fold = os_path.join(self.starting_folder, "configs")
        self.subfolderConfig_path = os_path.join(config_fold, 'x_configs')

    def load_config_file(self, config_file_path):
        with open(config_file_path, 'r') as file:
            self.config = yaml_safe_load(file)

        self.current_conf = self.config['current']

        self.opt_channels = int(self.config['opt_measurement']['channels'])
        self.max_stretch = float(self.config['opt_measurement']['max_stretch'])
        self.max_stretch_unit = self.config['opt_measurement']['max_stretch_unit']
        self.pre_strain = self.config['opt_measurement']['pre_strain']
        self.pre_strain_length = float(self.config['opt_measurement']['pre_strain_length'])
        self.pre_strain_unit = self.config['opt_measurement']['pre_strain_unit']

        self.calib_optical_sensitivity = float(self.config['calibration']['optical_sensitivity'])
        self.calib_optical_sens_tolerance = float(self.config['calibration']['optical_sens_tolerance'])
        self.number_of_steps = int(self.config['calibration']['number_of_steps'])

        self.calib_plot = self.config['calibration']['plot']
        self.slope_check = self.config['calibration']['slope_check']

        self.folder_main = check_file_path(self.config['save_data']['main_folder'], self.folder_main)
        # self.folder_main = self.config['save_data']['main_folder']
        self.folder_calibration_export = check_file_path(self.config['save_data']['calibration_export'], self.folder_calibration_export)
        # self.folder_calibration_export = self.config['save_data']['calibration_export']
        self.folder_db_export_folder = self.config['save_data']['db_folder']
        self.folder_statistics = self.config['save_data']['stats_folder']
        self.S_N = self.config['save_data']['S_N']
        self.export_local_server = self.config['save_data']['export_local_server']
        self.auto_export = self.config['save_data']['auto_export']

        self.serial_no_motor_control = self.config['benchtop']['serial_no_motor_control']
        self.stage_name = self.config['benchtop']['stage_name']
        self.stage_min_limit = 0
        self.stage_max_limit = float(self.config['benchtop']['stage_max_limit'])
        self.optical_sensor_mount_position = self.config['benchtop']['optical_sensor_mount_position']
        self.polling_rate = int(self.config['benchtop']['polling_rate'])

        return self.check_if_none()

    def save_config_file(self, current_conf, config_file_path):
        self.config['current'] = current_conf

        self.config['opt_measurement']['sensor_type'] = self.opt_sensor_type
        self.config['opt_measurement']['channels'] = self.opt_channels
        self.config['opt_measurement']['max_stretch'] = self.max_stretch
        self.config['opt_measurement']['max_stretch_unit'] = self.max_stretch_unit
        self.config['opt_measurement']['pre_strain'] = self.pre_strain
        self.config['opt_measurement']['pre_strain_length'] = self.pre_strain_length
        self.config['opt_measurement']['pre_strain_unit'] = self.pre_strain_unit

        self.config['calibration']['optical_sensitivity'] = self.calib_optical_sensitivity
        self.config['calibration']['optical_sens_tolerance'] = self.calib_optical_sens_tolerance
        self.config['calibration']['plot'] = self.calib_plot
        self.config['calibration']['slope_check'] = self.slope_check
        self.config['calibration']['number_of_steps'] = self.number_of_steps

        self.config['save_data']['main_folder'] = self.folder_main
        self.config['save_data']['calibration_export'] = self.folder_calibration_export
        self.config['save_data']['db_folder'] = self.folder_db_export_folder
        self.config['save_data']['stats_folder'] = self.folder_statistics
        self.config['save_data']['export_local_server'] = self.export_local_server
        self.config['save_data']['auto_export'] = self.auto_export
        self.config['save_data']['S_N'] = self.S_N

        self.config['benchtop']['serial_no_motor_control'] = self.serial_no_motor_control
        self.config['benchtop']['stage_name'] = self.stage_name
        self.config['benchtop']['stage_max_limit'] = self.stage_max_limit
        self.config['benchtop']['optical_sensor_mount_position'] = self.optical_sensor_mount_position
        self.config['benchtop']['polling_rate'] = self.polling_rate

        # set_read_write(config_file_path)

        with open(config_file_path, 'w') as file:
            yaml_dump(self.config, file)
        # set_read_only(config_file_path)

        return self.check_if_none()

    def check_if_none(self):
        def traverse(data):
            if data is None or data == '':
                return True
            if isinstance(data, dict):
                return any(traverse(value) for value in data.values())
            if isinstance(data, list):
                return any(traverse(item) for item in data)
            return False

        try:
            return traverse(self.config)
        except YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return True

    def default_config(self, sensor_type):
        documents_path = os_path.expanduser('~/Documents')

        main_folder_path = os_path.join(documents_path, 'Sylex_sensors_export')
        subfolderCalibrationData = os_path.join(main_folder_path, 'calibration')

        def_config = {
            'current': True,
            'benchtop': {
                'serial_no_motor_control': '00000000',
                'stage_name': None,
                'stage_max_limit': 0,
                'optical_sensor_mount_position': 0,
                'polling_rate': 100
            },
            'opt_measurement': {
                'sensor_type': "Strain",
                'sampling_rate': 800,
                'channels': 1,
                'max_stretch': 0.0,
                'max_stretch_unit': 'pm',
                'pre_strain': False,
                'pre_strain_length': 0,
                "pre_strain_unit": "pm",
            },
            'calibration': {
                'optical_sensitivity': 0,
                'optical_sens_tolerance': 0,
                'plot': 0,
                'slope_check': 1,
                'number_of_steps': 10
            },
            'save_data': {
                'main_folder': main_folder_path,
                'calibration_export': subfolderCalibrationData,
                'db_folder': None,
                'stats_folder': main_folder_path,
                'auto_export': True,
                'export_local_server': True,
                'S_N': 'measured_data.csv'
            },
        }
        return def_config

    def create_folders(self):
        if not os_path.exists(self.folder_main):
            # Create the main folder
            os_makedirs(self.folder_main)
        # Create the subfolders inside the main folder
        os_makedirs(self.folder_calibration_export, exist_ok=True)
        os_makedirs(self.subfolderConfig_path, exist_ok=True)

    def check_properties_for_none(self):
        for attribute, value in self.__dict__.items():
            if value is None:
                print(f"Property '{attribute}' contains None")
                return True
        print("No properties contain None")
        return False

    def create_config_file(self, yaml_name='default_config_strain.yaml'):
        config_file_path = os_path.join(self.subfolderConfig_path, yaml_name)
        new_conf = self.default_config(self.opt_sensor_type)
        with open(config_file_path, 'w') as file:
            yaml_dump(new_conf, file)

        return self.load_config_file(config_file_path), config_file_path

