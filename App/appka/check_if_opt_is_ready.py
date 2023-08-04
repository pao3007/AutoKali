import time
import PyQt5
from pyModbusTCP.client import ModbusClient

class ModbusReader(PyQt5.QtCore.QThread):

    def __init__(self, server_ip, server_port, unit_id, address, number_of_samples):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.unit_id = unit_id
        self.address = address
        self.number_of_samples = number_of_samples

    def run(self):
        while True:
            print()

    def get_samples(self):
        client = ModbusClient(host=self.server_ip, port=self.server_port, unit_id=self.unit_id)
        client.open()

        samples = []

        while len(samples) < self.number_of_samples:
            if client.is_open:
                # regs = client.read_holding_registers()  # Adjust the quantity to 2
                regs = client.read_input_registers(self.address, 2)
                if regs is not None:
                    # Assume the first register is the whole number and the second is the decimal part
                    sample = regs[0] + regs[1] / 10000  # Add them to form a floating point number
                    samples.append(sample)
            else:
                print("Connection lost... Reconnecting...")
                client.open()
            time.sleep(1/1000)  # Added polling rate

        client.close()
        return samples

# Then you would initialize ModbusReader like so:
modbus_thread = ModbusReader("127.0.0.1", 501, 1, 100, 4000)  # Adjust parameters as needed

modbus_thread.run()