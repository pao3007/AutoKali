import nidaqmx

# Check device connection
device_name = "cDAQ1Mod1"  # Replace with the appropriate device name
channel_name = "ai2"  # Replace with the desired channel name
is_device_connected = False

with nidaqmx.Task() as task:
    try:
        task.ai_channels.add_ai_voltage_chan(f"{device_name}/{channel_name}")
        is_device_connected = True
    except nidaqmx.DaqError as e:
        if device_name in str(e) and f"{device_name}/{channel_name}" in str(e):
            is_device_connected = False

# Check channel usage
channel_in_use = False

with nidaqmx.Task() as task:
    try:
        task.ai_channels.add_ai_voltage_chan(f"{device_name}/{channel_name}")
    except nidaqmx.DaqError as e:
        if device_name in str(e) and f"{device_name}/{channel_name}" in str(e):
            channel_in_use = True

# Print device and channel information
print("Device Information:")
print(f"Device: {device_name}")
print(f"Is Device Connected: {is_device_connected}")

print("\nChannel Information:")
print(f"Channel: {device_name}/{channel_name}")
print(f"Is Channel in Use: {channel_in_use}")
