import os

from AC_calibration_2FBG_edit import ACCalib_2ch

acc_yeet = ACCalib_2ch('242358_05_autoCalib',os.getcwd(),r'C:\Users\lukac\Documents\Sylex_sensors_export',
                  r'C:\Users\lukac\Documents\Sylex_sensors_export\optical_raw',
                  r'C:\Users\lukac\Documents\Sylex_sensors_export\reference_raw', 1.079511, 50, 800, 12800, "bandpass",
                  1, 1, 10, 100, 30, 50).start(False, 1.35, True, 0)

ACCalib_2ch('242358_05_autoCalib',os.getcwd(),r'C:\Users\lukac\Documents\Sylex_sensors_export',
                  r'C:\Users\lukac\Documents\Sylex_sensors_export\optical_raw',
                  r'C:\Users\lukac\Documents\Sylex_sensors_export\reference_raw', 1.079511, 50, 800, 12800, "bandpass",
                  1, 1, 10, 100, 30, 50).start(True, acc_yeet[1]/1000, True, acc_yeet[8])


# acc.start(True, acc_yeet[1]/1000, True)
# acc.start(False, 0, True)