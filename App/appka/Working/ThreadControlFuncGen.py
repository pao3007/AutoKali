from PyQt5.QtCore import QThread, pyqtSignal
from pyvisa import ResourceManager as pyvisa_ResourceManager, errors as visa_errors
from ThreadControlFuncGenStatements import ThreadControlFuncGenStatements
from definitions import kill_sentinel, start_sentinel_d, check_function_gen_connected


class ThreadControlFuncGen(QThread):
    connected_status = pyqtSignal(bool)
    step_status = pyqtSignal(str)
    set_btn = pyqtSignal()

    def __init__(self, generator_id: str, generator_sweep_time: int, generator_sweep_start_freq: int,
                 generator_sweep_stop_freq: int, generator_sweep_type: str, generator_max_mvpp: int,
                 thcfgs: ThreadControlFuncGenStatements, opt_project: str, opt_channels: int, sentinel_s_folder: str):
        super().__init__()
        self.generator_id = generator_id
        self.generator_sweep_time = generator_sweep_time
        self.generator_sweep_start_freq = generator_sweep_start_freq
        self.generator_sweep_stop_freq = generator_sweep_stop_freq
        self.generator_sweep_type = generator_sweep_type
        self.generator_max_vpp = generator_max_mvpp / 1000
        self.opt_project = opt_project
        self.thcfgs = thcfgs
        self.opt_channels = opt_channels
        self.generator_check = True
        self.sentinel_s_folder = sentinel_s_folder
        self.rm = None
        self.instrument = None

    def run(self):
        self.run_gen()
        try:
            print("TURNING OFF CONTROL GEN")
            self.instrument.write('OUTPut1:STATe OFF')
            self.rm.close()
        except Exception as e:
            print(e)

    def run_gen(self):
        self.step_status.emit("Starting the sensors test ")
        self.msleep(200)
        try:
            self.rm = pyvisa_ResourceManager()
            self.instrument = self.rm.open_resource(self.generator_id)
            self.instrument.write('OUTPut1:STATe OFF')
            self.instrument.write('SOURce1:FUNCtion SINusoid')
            self.instrument.write('SOURce1:FREQuency:MODE FIXed')
            self.instrument.write('SOURce1:FREQuency ' + str(self.generator_sweep_stop_freq / 2))
            self.instrument.write('SOURce1:VOLTage:LIMit:HIGH +' + str(self.generator_max_vpp))
            self.instrument.write('SOURce1:VOLTage:LIMit:STATe 0')
            self.instrument.write('SOURce1:VOLTage ' + str(self.generator_max_vpp / 5))
            self.instrument.write('TRIGger1:SOURce IMMediate')

            self.thcfgs.set_start_sens_test(True)
            self.instrument.write('OUTPut1:STATe ON')
            i = 0
            while not self.thcfgs.get_end_sens_test():
                self.step_status.emit("Testing sensors ")
                if self.thcfgs.get_emergency_stop() or not self.generator_check:
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(40)
                i += 1
                if i >= 5:
                    self.set_btn.emit()
            self.instrument.write('OUTPut1:STATe OFF')

            i = 0
            while i < 10:
                self.step_status.emit("Starting quick sweep test ")
                i += 1
                if self.thcfgs.get_emergency_stop() or not self.generator_check:
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(50)

            self.instrument.write('SOURce1:FREQuency:MODE SWEep')
            self.instrument.write('SOURce1:FUNCtion ' + str(self.generator_sweep_type))
            self.instrument.write('SOURce1:FREQuency:STARt ' + str(self.generator_sweep_start_freq))
            self.instrument.write('SOURce1:FREQuency:STOP ' + str(self.generator_sweep_stop_freq))
            self.instrument.write('SOURce1:VOLTage ' + str(self.generator_max_vpp))
            self.instrument.write('SOURce1:SWEep:TIME ' + str(5))
            self.instrument.write('TRIGger1:SOURce BUS')
            self.instrument.write('SOURce1:SWEep:SPACing LINear')  # LINear
            self.instrument.write('OUTPut1:STATe ON')
            self.instrument.write('TRIGger1')
            i = 0
            while i < 100:
                self.step_status.emit("Quick sweep test ")
                i += 1
                if self.thcfgs.get_emergency_stop() or not self.generator_check:
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(50)
            self.step_status.emit("Waiting for sentinel to start ")

            kill_sentinel(False, True)
            start_sentinel_d(self.opt_project, self.sentinel_s_folder)
            # self.thcfgs.set_sentinel_started(True)
            i = 0
            while i < 10:
                i += 1
                if self.thcfgs.get_emergency_stop() or not self.generator_check:
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(50)
            self.instrument.write('OUTPut1:STATe OFF')
            self.instrument.write('SOURce1:SWEep:TIME ' + str(self.generator_sweep_time))

            while not self.thcfgs.get_start_measuring():
                self.step_status.emit("Waiting for sentinel to start ")
                if self.thcfgs.get_emergency_stop():
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(50)

            i = 0

            while i < 10:
                self.step_status.emit("Measuring central wavelength ")
                if self.thcfgs.get_emergency_stop():
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(50)
                i += 1

            self.instrument.write('OUTPut1:STATe ON')

            i = 0
            while i < 20:
                self.step_status.emit("Starting the measurement ")
                if self.thcfgs.get_emergency_stop():
                    self.thcfgs.set_emergency_stop(True)
                    return
                self.msleep(50)
                i += 1
            self.instrument.write('TRIGger1')

            while not self.thcfgs.get_finished_measuring():
                self.step_status.emit("Measuring sensors responses for sweeping ")
                if self.thcfgs.get_emergency_stop():
                    return
                self.msleep(50)
            self.step_status.emit("Calibration ...")
        except visa_errors:
            self.step_status.emit("A VISA I/O error occurred. \nConnect or restart function generator")
            self.thcfgs.set_emergency_stop(True)
        except Exception as e:
            self.step_status.emit("Error occured : \n" + str(e))
            self.thcfgs.set_emergency_stop(True)
