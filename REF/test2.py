import nidaqmx
system = nidaqmx.system.System.local()

devices = system.devices
device_name = "cDAQ1Mod1"  # Replace with the appropriate device name

if device_name in devices:
    print(f"Device '{device_name}' found.")
else:
    print(f"Device '{device_name}' not found. Please ensure it is connected.")
    # Additional error handling or graceful termination can be performed here.

