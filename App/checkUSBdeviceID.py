import wmi

# Initialize the WMI interface
c = wmi.WMI()

def check_device_connected(vendor_id):
    # Query connected USB devices
    for usb in c.Win32_USBControllerDevice():
        try:
            device = usb.Dependent
            # The string to parse is like 'USB\\VID_045E&PID_07A5&MI_02\\7&37207CFF&0&0002'
            # VID is the vendor id
            device = device.DeviceID
            vid_start = device.find('VID_') + 4
            vid_end = device.find('&', vid_start)
            v_id = device[vid_start:vid_end]

            # Check if this device's Vendor ID matches the one we're looking for
            if v_id.upper() == vendor_id.upper():
                return True
        except Exception as e:
            pass
    return False

vendor_id = '0951'  # replace with your device's vendor ID
print(check_device_connected(vendor_id))



