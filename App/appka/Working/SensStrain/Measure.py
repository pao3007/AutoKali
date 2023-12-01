from SettingsParams import MySettings
from TMCStatements import TMCStatements
from ThreadMotorControl import ThreadMotorControl
import time
from os import getcwd


class OptMeasure:

    def __init__(self):
        self.my_settings = MySettings(getcwd())
        self.tmcs = TMCStatements()
        self.tmc = None

        self.tmc = ThreadMotorControl(self.my_settings, self.tmcs)
        self.tmc.start()

        self.my_settings.stage_max_limit = 50.0
        # self.my_settings.device_settings_name = 'LNR502E'
        self.my_settings.stage_name = 'LNR50SE/M'
        self.my_settings.serial_no_motor_control = "40847135"
        self.my_settings.optical_sensor_mount_position = 45.0

    def init_bench(self):
        self.tmcs.init_home = True
        while not self.tmcs.init_home_finished:
            time.sleep(0.05)
        self.tmcs.reset()

    def init_exit(self):
        self.tmcs.init_exit = True
        while not self.tmcs.init_exit_finished:
            time.sleep(0.05)
        self.tmcs.reset()

    def start_calibration(self):
        self.tmcs.pos = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 20.0, 15.0, 10.0, 5.0, 0.0]
        steps = len(self.tmcs.pos)
        self.tmcs.in_position = True

        while self.tmcs.step < steps:
            if self.tmcs.init_done:
                self.tmcs.start = True
                if self.tmcs.in_position:
                    self.tmcs.in_position = False
                    print("ROBIM SI VECI")
                    print(self.tmcs.step)
                    # meranie vlnovej dlzky....
                    time.sleep(1)
                    if self.tmcs.step+1 == steps:
                        self.tmcs.continue_flag = False
                        break
                    else:
                        self.tmcs.continue_flag = True
                        self.tmcs.step += 1
            time.sleep(0.05)
        self.tmcs.home = True
        while not self.tmcs.home_finished:
            time.sleep(0.05)
        self.tmcs.finished = True
        self.tmcs.reset()

    def test(self):
        self.tmcs.move_to_position = 25.0
        self.tmcs.move_to_action = True
        while not self.tmcs.move_to_action_finished:
            time.sleep(0.05)
        print("WAIT")
        time.sleep(5.05)
        self.tmcs.move_by_length = 1.0
        self.tmcs.move_by_direction = -1
        self.tmcs.move_by_action = True
        while not self.tmcs.move_by_action_finished:
            time.sleep(0.05)
        print("WAIT")
        time.sleep(5.05)
        self.tmcs.move_by_direction = 1
        self.tmcs.move_by_action = True
        while not self.tmcs.move_by_action_finished:
            time.sleep(0.05)


if __name__ == "__main__":
    om = OptMeasure()
    om.init_bench()
    print("INIT HOME DONE")
    time.sleep(1)
    print("START MOVING")
    om.start_calibration()
    time.sleep(1)
    om.init_exit()
