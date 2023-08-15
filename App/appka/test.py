from pyvisa import ResourceManager as pyvisa_ResourceManager
generator_sweep_stop_freq = 200
generator_max_vpp = 0.01
# generator_id = 'USB0::0x2A8D::0x8C01::CN63070058::INSTR'
# generator_id = 'TCPIP0::10.88.5.166::5025::SOCKET'
# generator_id = 'TCPIP0::10.88.5.166::inst0::INSTR'

rm = pyvisa_ResourceManager()
instruments = rm.list_resources()
print(instruments)
# instrument = rm.open_resource(generator_id)
# instrument.write('OUTPut1:STATe ON')
# instrument.write('*IDN?')
# instrument.timeout = 20000
# response = instrument.read()
# print(response)
# instrument.close()

# rm = pyvisa_ResourceManager()
#
# instrument = rm.open_resource(generator_id)
#
# instrument.write('OUTPut1:STATe OFF')
#
# instrument.write('SOURce1:FUNCtion SINusoid')
# instrument.write('SOURce1:FREQuency:MODE FIXed')
# instrument.write('SOURce1:FREQuency ' + str(generator_sweep_stop_freq))
# instrument.write('SOURce1:VOLTage ' + str(generator_max_vpp))
# instrument.write('TRIGger1:SOURce IMMediate')
#
# instrument.write('OUTPut1:STATe ON')
# instrument.write('TRIGger1')
