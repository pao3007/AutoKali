import yaml, os

documents_path = os.path.expanduser('~/Documents')
main_folder_name = 'Sylex_sensors_export'
main_folder_path = os.path.join(documents_path, main_folder_name)

config_data = {
    'ref_device': {
        'channel': None,
        'name': 'cDAQ1Mod1',
        'measure_time': 25,
    },
    'ref_measurement': {
        'number_of_samples_per_channel': 64000,
        'sample_rate': 12800
    },
    'opt_measurement': {
        'sensor_type': 'accelerometer',
        'sampling_rate': 800,
        'project': 'test.ssd',
    },
    'calibration': {
        'gain_mark': 150,
        'optical_sensitivity': 0,
        'filter_data': 'high-pass',
        'plot': 0,
        'downsample': 1,
        'do_spectrum': 1,
    },
    'save_data': {
        'main_folder': main_folder_path,
        'ref_export': 'C:/Users/lukac/Documents/Sylex_sensors_export/reference',
        'ref_export_raw': 'C:/Users/lukac/Documents/Sylex_sensors_export/reference_raw',
        'opt_export': 'C:/Users/lukac/Documents/Sylex_sensors_export/optical',
        'opt_export_raw': 'C:/Users/lukac/Documents/Sylex_sensors_export/optical_raw',
        'calibration_export': 'C:/Users/lukac/Documents/Sylex_sensors_export/calibration',
        'sentinel_folder': 'C:/Users/lukac/Desktop/Sylex/Sentinel/Sentinel2_Dynamic_v0_4_1/Sentinel2_Dynamic_v0_4_1',
        'S_N': 'measured_data.csv'
    }
}

with open('testting.yaml', 'w') as file:
    yaml.dump(config_data, file)
