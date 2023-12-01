from definitions import fetch_wavelengths_peak_logger
from time import sleep

while True:
    res, wl = fetch_wavelengths_peak_logger(True)
    print(res)
    print(wl)
    sleep(0.2)
