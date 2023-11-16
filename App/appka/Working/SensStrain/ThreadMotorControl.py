from PyQt5.QtCore import QThread, pyqtSignal
from SensStrain.SettingsParams import MySettings
import clr
from SensStrain.TMCStatements import TMCStatements
import pythonnet

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import *
from System import Decimal


class ThreadMotorControl(QThread):
    update_position = pyqtSignal(float)

    def __init__(self, my_settings: MySettings, tmcs: TMCStatements):
        super().__init__()
        self.check_pos_thread = None
        self.chan_settings = None
        self.channel_config = None
        self.serial_no = None
        self.my_settings = my_settings
        self.polling_rate = my_settings.polling_rate
        self.device = None
        self.channel = None
        self.tmcs = tmcs
        self.sim = SimulationManager.Instance
        self.dmCLI = DeviceManagerCLI

    def run(self):
        # self.sim.InitializeSimulations()
        try:
            self.init_motor_control()
            self.start_control()
        except Exception as e:
            print("LOOP :", e)
            self.tmcs.termination = True
            self.tmcs.termination_pos = True
            self.tmcs.emergency_stop = True
            self.tmcs.error = True

        try:
            print("STOP POLLING")
            self.channel.StopPolling()
        except Exception as e:
            print(e)
        try:
            print("DISCONNECT DEVICE")
            self.device.Disconnect()
        except Exception as e:
            print(e)
        # self.sim.UninitializeSimulations()

    def init_exit(self):
        if self.tmcs.init_exit:
            print("START HOMING FOR EXIT")
            self.channel.MoveTo(Decimal(0), 60000)
            self.tmcs.init_exit_finished = True
            print("FINISHED HOMING")

    def init_home(self):
        print("START HOMING FOR INIT")
        self.channel.Home(60000)
        self.channel.MoveTo(Decimal(self.my_settings.stage_max_limit), 60000)
        self.tmcs.inc = float(self.my_settings.stage_max_limit) / float(self.channel.GetPositionCounter())
        self.channel.MoveTo(Decimal(self.my_settings.optical_sensor_mount_position), 10000)
        self.tmcs.init_home_finished = True
        print("FINISHED HOMING")

    def start_control(self):
        self.check_pos_thread = CheckPositionThread(self.tmcs, self)
        self.check_pos_thread.start()
        while not self.tmcs.termination and not self.tmcs.emergency_stop:

            if self.tmcs.start and not self.tmcs.finished:
                if self.tmcs.continue_flag:
                    print("\nSTART MOVING TO POSITION")
                    self.channel.MoveTo(Decimal(self.my_settings.optical_sensor_mount_position-self.tmcs.pos[self.tmcs.step]), 10000)
                    self.msleep(50)
                    current_pos = self.channel.GetPositionCounter()*self.tmcs.inc
                    self.tmcs.output_bench.append(current_pos)
                    # print(current_pos)
                    # self.update_position.emit(current_pos)
                    self.tmcs.in_position = True
                    self.tmcs.continue_flag = False
                    print("FINISHED MOVING TO POSITION\n")
                if self.tmcs.home:
                    print("START HOMING FOR CALIBRATION")
                    self.channel.MoveTo(Decimal(self.my_settings.optical_sensor_mount_position), 60000)
                    self.tmcs.home_finished = True
                    self.tmcs.home = False
                    print("FINISHED HOMING")
            elif self.tmcs.init_home:
                self.init_home()
                self.tmcs.init_home = False
            elif self.tmcs.init_exit:
                self.init_exit()
                self.tmcs.init_exit = False
                self.tmcs.termination = True
                break
            elif self.tmcs.move_by_action:
                self.tmcs.move_by_action = False
                print("\nSTART MOVING TO RELATIVE POSITION:", self.tmcs.move_by_length*self.tmcs.move_by_direction)
                self.channel.SetMoveRelativeDistance(Decimal(self.tmcs.move_by_length*self.tmcs.move_by_direction))
                self.channel.MoveRelative(10000)
                self.tmcs.move_by_action_finished = True
                print("FINISHED MOVING TO RELATIVE POSITION\n")
            elif self.tmcs.move_to_action:
                self.tmcs.move_to_action = False
                print("\nSTART MOVING TO ABSOLUTE POSITION:", self.tmcs.move_to_position)
                self.channel.MoveTo(Decimal(self.tmcs.move_to_position), 60000)
                self.tmcs.move_by_action_finished = True
                print("FINISHED MOVING TO ABSOLUTE POSITION\n")
            self.msleep(self.polling_rate*2)
            print("LOOP")
            # print(self.channel.DevicePosition)
            if self.tmcs.emergency_stop:
                self.channel.StopImmediate()

    def init_motor_control(self):
        print("INIT MOTOR START")
        self.dmCLI.BuildDeviceList()

        # create new device
        self.serial_no = self.my_settings.serial_no_motor_control  # Replace this line with your device's serial number
        print(self.serial_no)
        # Connect, begin polling, and enable
        self.device = BenchtopStepperMotor.CreateBenchtopStepperMotor(self.serial_no)
        self.device.Connect(self.serial_no)
        self.msleep(1000)  # wait statements are important to allow settings to be sent to the device

        # For benchtop devices, get the channel
        self.channel = self.device.GetChannel(1)
        # Ensure that the device settings have been initialized
        if not self.channel.IsSettingsInitialized():
            self.channel.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert self.channel.IsSettingsInitialized() is True

        # Start polling and enable

        self.polling_rate = self.my_settings.polling_rate
        print(self.polling_rate)
        self.channel.StartPolling(self.polling_rate)
        self.msleep(1000)
        self.channel.EnableDevice()
        self.msleep(1000)  # Wait for device to enable

        # Get Device Information and display description
        device_info = self.channel.GetDeviceInfo()
        # print(device_info.Description)

        # Load any configuration settings needed by the controller/stage
        self.channel_config = self.channel.LoadMotorConfiguration(self.serial_no) # If using BSC203, change serial_no to channel.DeviceID.
        self.chan_settings = self.channel.MotorDeviceSettings
        self.channel.GetSettings(self.chan_settings)
        print(self.my_settings.stage_name)
        self.channel_config.DeviceSettingsName = self.my_settings.stage_name

        self.channel_config.UpdateCurrentConfiguration()
        self.msleep(500)
        self.tmcs.init_done = True
        print("INIT MOTOR FINISHED")


class CheckPositionThread(QThread):

    def __init__(self, tmcs, parent: ThreadMotorControl):
        super().__init__()
        self.tmcs = tmcs
        self.parent = parent

    def run(self):
        self.check_pos()

    def check_pos(self):
        while not self.tmcs.termination_pos and not self.tmcs.emergency_stop:
            self.msleep(self.parent.polling_rate*2)
            self.tmcs.current_position = self.parent.channel.GetPositionCounter() * self.tmcs.inc
            self.parent.update_position.emit(self.tmcs.current_position)
