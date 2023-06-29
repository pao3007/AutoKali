import nidaqmx.system
system = nidaqmx.system.System.local()

for device in system.devices:
        print(device)




