from numpy import mean as np_mean, abs as np_abs, array as np_array, max as np_max
from PyQt5.QtCore import QThread, pyqtSignal
from scipy.stats import linregress

from DatabaseCom import DatabaseCom
from SensStrain.SettingsParams import MySettings
from SensStrain.TMCStatements import TMCStatements
from SensStrain.MyMainWindow import MyMainWindow
from definitions import linear_regression


class OptMeasure(QThread):
    update = pyqtSignal(float)

    def __init__(self, my_settings: MySettings, tmcs: TMCStatements, calib_window: MyMainWindow):
        super().__init__()
        self.my_settings = my_settings
        self.tmcs = tmcs

        self.my_settings.stage_max_limit = 50.0
        # self.my_settings.device_settings_name = 'LNR502E'
        self.my_settings.stage_name = 'LNR50SE/M'
        self.my_settings.serial_no_motor_control = "40847135"
        self.my_settings.optical_sensor_mount_position = 45.0
        self.calib_window = calib_window
        self.temp_wl_1 = []
        self.temp_wl_2 = []
        self.unit_map = {
            "mm": 1,
            "um": 1e-03,
            "nm": 1e-06,
            "pm": 1e-09
            # "fm": 1e-12
        }
        self.calibration_results = None

    def run(self):
        self.tmcs.opt_wls.clear()
        self.tmcs.ref_pos.clear()
        self.tmcs.disable_usb_check = True
        self.start_calibration()
        self.tmcs.disable_usb_check = False
        self.calibration()

    def start_calibration(self):
        self.tmcs.disable_usb_check = True
        if self.my_settings.pre_strain:
            self.tmcs.move_by_length = self.my_settings.pre_strain_length
            self.tmcs.move_by_direction = -1
            self.tmcs.move_by_action = True
            while not self.tmcs.move_by_action_finished:
                self.msleep(50)
            self.msleep(500)
        steps = len(self.tmcs.pos)
        self.tmcs.in_position = True

        while self.tmcs.step < steps:
            if self.tmcs.init_done:
                self.tmcs.start = True
                if self.tmcs.in_position:
                    self.tmcs.in_position = False
                    self.msleep(500)
                    i = 0
                    self.temp_wl_1.clear()
                    while i < 5:
                        tmp = self.calib_window.sensor_opt_value
                        if len(tmp) == 1:
                            self.temp_wl_1.append(tmp)
                        else:
                            self.temp_wl_1.append(tmp[0])
                            self.temp_wl_2.append(tmp[1])
                        self.msleep(300)
                    if len(self.temp_wl_2) == 0:
                        opt = np_mean(self.temp_wl_1)
                        self.tmcs.opt_wls_1.append(opt)
                    else:
                        opt = np_mean(self.temp_wl_1)
                        self.tmcs.opt_wls_1.append(opt)
                        opt = np_mean(self.temp_wl_2)
                        self.tmcs.opt_wls_2.append(opt)

                    self.tmcs.ref_pos.append(self.tmcs.current_position)
                    if self.tmcs.step + 1 == steps:
                        self.tmcs.continue_flag = False
                        break
                    else:
                        self.tmcs.continue_flag = True
                        self.tmcs.step += 1
                        self.update.emit(self.tmcs.step)
            self.msleep(250)
        self.tmcs.home = True
        while not self.tmcs.home_finished:
            self.msleep(250)
        self.tmcs.finished = True
        self.tmcs.reset()
        self.tmcs.disable_usb_check = False

    def calculate_step_positions(self):
        step_value = self.my_settings.max_stretch / self.my_settings.number_of_steps
        unit = self.my_settings.max_stretch_unit
        unit_value = self.unit_map.get(unit, 4)
        increasing = [i * step_value * unit_value for i in range(self.my_settings.number_of_steps + 1)]
        decreasing = increasing[:-1][::-1]
        self.tmcs.pos = (increasing + decreasing) * unit_value

    def calibration(self):
        def save_data():
            pass

        def load_params_to_export(FFL=None):
            CWL1 = cw_opt_strain
            CWL2 = cw_opt_temp
            strain_coeffA = strain_coeff_A
            FFL = FFL * 1000
            ERROR = max_error
            max_strain = MAXIMUM_STRAIN
            r2_regression = r2
            reg_points = len(self.tmcs.opt_wls_1)
            slope_samples = [slope * x + intercept for x in micro_strain]

            return [CWL1, CWL2, strain_coeffA, FFL, ERROR, max_strain, r2_regression, reg_points, slope_samples, micro_strain, relative_wl_change]

        db = DatabaseCom(self.my_settings.starting_folder)
        FFL = db.get_strain_info(self.calib_window.s_n_export)
        MAXIMUM_STRAIN = 10000  # ???

        cw_opt_strain = self.tmcs.opt_wls_1[0]
        cw_opt_temp = self.tmcs.opt_wls_2[0] if len(self.tmcs.opt_wls_2) != 0 else None
        pos0_ref = self.tmcs.ref_pos[0]

        arr_opt = self.tmcs.opt_wls_1 - cw_opt_strain
        arr_ref = np_abs(self.tmcs.ref_pos - pos0_ref)

        micro_strain = -(arr_ref / FFL)*1000
        relative_wl_change = arr_opt / cw_opt_strain
        slope, intercept, r_value, p_value, std_err = linregress(micro_strain, relative_wl_change)

        strain_coeff_A = slope
        calc_strain_change = relative_wl_change/strain_coeff_A
        abs_error = np_abs(micro_strain - calc_strain_change)
        perc_error = (abs_error/MAXIMUM_STRAIN)*100
        max_error = np_max(perc_error)
        r2 = r_value*r_value

        self.calibration_results = load_params_to_export(FFL)

        save_data()
