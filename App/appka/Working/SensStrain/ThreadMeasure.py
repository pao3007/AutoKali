from numpy import mean as np_mean
from PyQt5.QtCore import QThread, pyqtSignal
from SensStrain.SettingsParams import MySettings
from SensStrain.TMCStatements import TMCStatements
from SensStrain.MyMainWindow import MyMainWindow


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
        self.temp_wl = []
        self.unit_map = {
            "mm": 1,
            "um": 1e-03,
            "nm": 1e-06,
            "pm": 1e-09
            # "fm": 1e-12
        }

    def run(self):
        self.tmcs.opt_wls.clear()
        self.tmcs.ref_pos.clear()
        self.tmcs.disable_usb_check = True
        self.start_calibration()
        self.tmcs.disable_usb_check = False
        self.calibration()

    def start_calibration(self):
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
                    self.temp_wl.clear()
                    while i < 10:
                        self.temp_wl.append(self.calib_window.sensor_opt_value)
                        self.msleep(100)
                    opt = np_mean(self.temp_wl)
                    self.tmcs.opt_wls.append(opt)
                    self.tmcs.ref_pos.append(self.tmcs.current_position)
                    if self.tmcs.step+1 == steps:
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

    def calculate_step_positions(self):
        step_value = self.my_settings.max_stretch / self.my_settings.number_of_steps
        unit = self.my_settings.max_stretch_unit
        unit_value = self.unit_map.get(unit, 4)
        increasing = [i * step_value * unit_value for i in range(self.my_settings.number_of_steps + 1)]
        decreasing = increasing[:-1][::-1]
        self.tmcs.pos = (increasing + decreasing) * unit_value

    def calibration(self):
        self.save_data()

    def save_data(self):
        pass
