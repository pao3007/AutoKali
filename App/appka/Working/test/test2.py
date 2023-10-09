import numpy as np
from matplotlib import pyplot as plt


def load_two_columns_from_csv(file_path):
    column1_data = []
    column2_data = []

    with open(file_path, 'r') as file:
        for line in file:
            column1, column2 = line.strip().split()
            column1_data.append(column1)
            column2_data.append(column2)

    x = np.array(column1_data, dtype=float)
    y = np.array(column2_data, dtype=float)
    return x, y


def linear_regression(x, y):
    n = len(x)
    m = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x ** 2) - (np.sum(x)) ** 2)
    b = (np.sum(y) - m * np.sum(x)) / n

    return m, b


if __name__ == "__main__":
    file_path = r"C:\Users\PC\Documents\Sylex_sensors_export\optical_raw\242355_0011.csv"

    col1_data, col2_data = load_two_columns_from_csv(file_path)
    col1_data = col1_data - np.mean(col1_data[50:100])
    col2_data = col2_data - np.mean(col2_data[50:100])
    # Linear regression for the first column against index
    index_values = np.array(range(len(col1_data)), dtype=float)  # Convert range to NumPy array
    slope1, intercept1 = linear_regression(index_values, col1_data)
    slope1 = slope1

    print(f"For first column - Slope: {slope1}, Intercept: {intercept1}")

    # Linear regression for the second column against index
    slope2, intercept2 = linear_regression(index_values, col2_data)

    print(f"For second column - Slope: {slope2}, Intercept: {intercept2}")
    print(col1_data)

    # index_values = np.arange(len(col1_data))
    #
    # # Perform linear regression
    # coefficients = np.polyfit(index_values, col1_data, 1)  # 1 for linear
    # slope, intercept = coefficients
    #
    # # Generate a fitted line
    # fitted_line = slope * index_values + intercept
    #
    # # Plotting
    # plt.scatter(index_values, col1_data, label='Measured Wavelengths', color='b')
    # plt.plot(index_values, fitted_line, label=f'Fitted Line: y={slope*10e6:.2f}x + {intercept:.2f}', color='r')
    # plt.xlabel('Index')
    # plt.ylabel('Wavelength (nm)')
    # plt.legend()
    # plt.show()

    # Visualization
    plt.figure(figsize=(12, 6))

    slope_samp = [slope1 * x + intercept1 for x in index_values]
    diff = np.abs(slope_samp[0]-slope_samp[-1])
    print(f"DIFF: {diff} | {slope_samp[0]} a {slope_samp[-1]}")
    plt.subplot(2, 1, 1)
    plt.plot(index_values, col1_data, label='Data Points (Column 1)')
    plt.plot(index_values, slope_samp, color='red',
             label=f'y={slope1*10e6}')
    plt.xlabel('Index')
    plt.ylabel('Column 1 Data')
    plt.legend()

    slope_samp2 = [slope2 * x + intercept2 for x in index_values]
    diff2 = np.abs(slope_samp2[0]-slope_samp2[-1])
    print(f"DIFF2: {diff2}")
    plt.subplot(2, 1, 2)
    plt.plot(index_values, col2_data, label='Data Points (Column 2)')
    plt.plot(index_values, slope_samp2, color='red',
             label=f'y={slope2*10e6}')
    plt.xlabel('Index')
    plt.ylabel('Column 2 Data')
    plt.legend()

    plt.tight_layout()
    plt.show()

    # mean_wavelength = np.mean(col2_data)
    # median_wavelength = np.median(col2_data)
    #
    # if np.isclose(mean_wavelength, median_wavelength, atol=1e-2):
    #     print("The distribution of wavelengths is likely symmetrical.")
    # else:
    #     print("The distribution of wavelengths is likely not symmetrical.")
    #
    # # Create histogram for visualization
    # plt.hist(col2_data, bins='auto', alpha=0.7, color='blue')
    # plt.axvline(mean_wavelength, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_wavelength}')
    # plt.axvline(median_wavelength, color='green', linestyle='dashed', linewidth=1, label=f'Median: {median_wavelength}')
    # plt.xlabel('Wavelength (nm)')
    # plt.ylabel('Frequency')
    # plt.legend()
    # plt.show()

    print(abs(slope1)*10e6)
    print(abs(slope2)*10e6)
