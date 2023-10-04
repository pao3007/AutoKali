import serial.tools.list_ports


def list_com_ports():
    com_ports = serial.tools.list_ports.comports()
    coms = []
    for port in com_ports:
        coms.append(port.manufacturer)
    return coms


if __name__ == "__main__":
    print(list_com_ports())

