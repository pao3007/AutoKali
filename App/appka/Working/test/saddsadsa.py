import pyvisa

rm = pyvisa.ResourceManager(r"C:\Windows\System32\visa64.dll")
devices = rm.list_resources()
print(devices)