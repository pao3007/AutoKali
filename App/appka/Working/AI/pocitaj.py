import re

import joblib
import pandas as pd
import torch
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from LSTMModel import LSTMModel


def load_dataset(file, diff_folder="datasets"):
    def extract_sensitivity_from_csv(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                # Use regular expression to match the line containing 'Sensitivity'
                if re.search(r"# Sensitivity\s*:", line):
                    # Get the next line that contains the sensitivity value
                    sensitivity_line = lines[lines.index(line) + 1].strip()
                    # Extract the numerical value using regex
                    sensitivity_value = re.findall(r"[\d.]+", sensitivity_line)[0]
                    return float(sensitivity_value)

    ref = pd.read_csv(fr"./{diff_folder}/{file}_ref.csv", header=None, usecols=[0])
    df = pd.read_csv(fr"./{diff_folder}/{file}_opt.csv", delim_whitespace=True, header=None)
    sens = extract_sensitivity_from_csv(fr"./{diff_folder}/{file}_cal.csv")
    col1 = np.array(df[0])
    cw1 = np.mean(col1[50:100])
    col2 = np.array(df[1])
    cw2 = np.mean(col2[50:100])
    opt = -(col1 - col2) + (cw1 - cw2)

    opt = opt[(sampling_rate_opt*2):(sampling_rate_opt*2)+(sampling_rate_opt*8)]
    ref = ref[(sampling_rate_ref*2):(sampling_rate_ref*2)+(sampling_rate_ref*8)]

    # Create an array for the new resampled dataset
    resampled_ref = np.interp(
        np.linspace(0, len(ref) - 1, len(opt)),
        np.arange(len(ref)),
        ref.values.flatten()
    )
    return opt, resampled_ref, sens


sampling_rate_opt = 800
sampling_rate_ref = 12800
scaler = joblib.load('scaler.pkl')

optical_sensor_new, reference_sensor_new, sens = load_dataset("242354_0009", diff_folder="datasets")

# You should use the same scaler object that you used for your training data to transform your new data.
# DO NOT fit the scaler again. Use the same scaler to transform (i.e., only use `transform` method)
reference_sensor_new_scaled = scaler.transform(reference_sensor_new.reshape(-1, 1))
optical_sensor_new_scaled = scaler.transform(optical_sensor_new.reshape(-1, 1))

# Prepare new data for LSTM model
X_new = np.hstack((reference_sensor_new_scaled, optical_sensor_new_scaled))

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# Convert to PyTorch tensor and move to device
X_new_tensor = torch.FloatTensor(X_new).to(device).unsqueeze(1)
input_dim = 2  # Number of features (reference and optical sensor data)
hidden_dim = 50
# Make sure the model is in evaluation mode
model = LSTMModel(input_dim, hidden_dim)
model = model.to(device)  # Don't forget to move the model to the device where you plan to run it
model_name = "model_sens_2ch_2"
model_save_path = f"./modely/{model_name}"
# Load the model parameters from the saved state_dict
model.load_state_dict(torch.load(model_save_path))
model.eval()

# Make predictions on new data
with torch.no_grad():
    predicted_sensitivity_new = model(X_new_tensor).cpu()

# Convert predictions to numpy array
predicted_sensitivity_new_np = predicted_sensitivity_new.numpy()

print(predicted_sensitivity_new_np, " / ", sens)
