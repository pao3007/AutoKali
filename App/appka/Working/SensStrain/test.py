import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import linregress

from definitions import linear_regression


def lin_regresion(x, y):
    # index_values = np_array(range(len(arr_sens)), dtype=float)  # Convert range to NumPy array
    slope, intercept = linear_regression(x, y)
    return slope

arr_ref = [0,
           -49.3,
           -98.6,
           -147.9,
           -197.4,
           -246.9,
           -296.2,
           -345.6,
           -394.8,
           -444.4,
           -395.7,
           -346.4,
           -297.2,
           -248.1,
           -198.8,
           -149.6,
           -100.3,
           -51.1]


values = """
1535,529175
1536,062012
1536,594971
1537,131226
1537,661133
1538,199951
1538,733765
1539,268799
1539,802979
1540,341187
1539,806885
1539,269043
1538,731201
1538,197754
1537,660156
1537,126709
1536,587646
1536,055176
"""
MAXIMUM_STRAIN = 10000
FFL = 0.11
# Replace commas with dots and split the string into a list
values_list = values.strip().replace(',', '.').split('\n')

# Convert each value to float and store it in a new list
opt_wls_1 = [float(value) for value in values_list]
cw_opt_strain = opt_wls_1[0]
arr_opt = np.array(opt_wls_1) - cw_opt_strain
arr_ref = np.array(arr_ref)/1000
micro_strain = (arr_ref / FFL) * 1000
relative_wl_change = arr_opt / cw_opt_strain
slope, intercept, r_value, p_value, std_err = linregress(micro_strain, relative_wl_change)
strain_coeff_A = slope
calc_strain_change = relative_wl_change / strain_coeff_A
abs_error = np.abs(micro_strain - calc_strain_change)
perc_error = (abs_error / MAXIMUM_STRAIN) * 100
max_error = np.max(perc_error)

print(r_value*r_value)

slope_samp1 = [slope * x + intercept for x in micro_strain]

plt.figure(figsize=(12, 6))

plt.scatter(micro_strain, relative_wl_change, label='Kĺzavý priemer', color='blue')
plt.plot(micro_strain,slope_samp1, label='Kĺzavý priemer', color='red')
print(slope_samp1)
plt.title('Priebeh tepovej frekvencie, kĺzavý priemer a filtrované dáta')
plt.xlabel('Čas (s)')
plt.ylabel('Tepová frekvencia (údery/min)')
plt.legend()
plt.grid(True)
plt.show()
