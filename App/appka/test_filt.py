import os

from AC_calibration_1FBG_v3 import ACCalib_1ch

acc = ACCalib_1ch('123',os.getcwd(),r'C:\Users\lukac\Documents\Sylex_sensors_export',
                  r'C:\Users\lukac\Documents\Sylex_sensors_export\optical_raw',
                  r'C:\Users\lukac\Documents\Sylex_sensors_export\reference_raw', 1.079511, 150, 800, 12800, "bandpass",
                  1, 1, 0, 10, 100, 10, 300)

acc.start(True)