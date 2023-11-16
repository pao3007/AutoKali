import os
import time
import sys
import clr
import pythonnet

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.Benchtop.StepperMotorCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import *
from System import Decimal


def main():
    """The main entry point for the application"""

    # Uncomment this line if you are using


    try:
        SimulationManager.Instance.InitializeSimulations()
        DeviceManagerCLI.BuildDeviceList()

        # create new device
        serial_no = "40847135"  # Replace this line with your device's serial number

        # Connect, begin polling, and enable
        device = BenchtopStepperMotor.CreateBenchtopStepperMotor(serial_no)
        device.Connect(serial_no)
        time.sleep(0.25)  # wait statements are important to allow settings to be sent to the device

        # For benchtop devices, get the channel
        channel = device.GetChannel(1)
        print("INIT DEV SETTINGS")
        # Ensure that the device settings have been initialized
        if not channel.IsSettingsInitialized():
            channel.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert channel.IsSettingsInitialized() is True

        # Start polling and enable
        channel.StartPolling(50)  #250ms polling rate
        print("SLEEP")
        time.sleep(1)
        channel.EnableDevice()
        time.sleep(0.25)  # Wait for device to enable

        # Get Device Information and display description
        device_info = channel.GetDeviceInfo()

        # Load any configuration settings needed by the controller/stage
        channel_config = channel.LoadMotorConfiguration(serial_no) # If using BSC203, change serial_no to channel.DeviceID.
        chan_settings = channel.MotorDeviceSettings
        channel.GetSettings(chan_settings)
        channel_config.DeviceSettingsName = 'LNR50SE/M'
        channel_config.UpdateCurrentConfiguration()
        channel.GetSettings(chan_settings)
        print(channel_config)

        # channel.SetSettings(chan_settings, True, False)

        # Get parameters related to homing/zeroing/other

        # Home or Zero the device (if a motor/piezo)
        # print("Homing Motor")
        # channel.Home(60000)
        # print("Done")
        # # Move the device to a new position
        # print("MOVING")
        channel.SetMoveRelativeDistance(Decimal(20.0))
        # channel.MoveRelative(10000)
        #
        inc = 1/411648

        # channel.MoveRelative(-1)

        time.sleep(2)
        print("Done")

        # Stop Polling and Disconnect

    except Exception as e:
        # this can be bad practice: It sometimes obscures the error source
        print("exception:",e)
    try:
        channel.StopPolling()
    except:
        pass
    try:
        device.Disconnect()
    except:
        pass

    # Uncomment this line if you are using Simulations
    SimulationManager.Instance.UninitializeSimulations()
    ...


if __name__ == "__main__":
    main()