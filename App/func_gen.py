import pyvisa
#
# rm = pyvisa.ResourceManager()
# devices = rm.list_resources()
#
# for device in devices:
#     print(device)

rm = pyvisa.ResourceManager()

# Connect to the device
instrument = rm.open_resource('USB0::0x2A8D::0x8C01::CN63070058::INSTR')

# Send command to turn ON channel 1
# instrument.write('OUTPut1:STATe ON')
# instrument.write('TRIGger1')
instrument.write('SOURce1:FUNCtion SINE')
instrument.write('SOURce1:FREQuency:STARt 5')
instrument.write('SOURce1:FREQuency:STOP 200')
instrument.write('SOURce1:VOLTage 0.04')
instrument.write('SOURce1:SWEep:TIME 20')




# Close the connection
instrument.close()