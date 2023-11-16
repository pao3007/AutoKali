import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.model_selection import train_test_split
import tensorflow as tf
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset


def load_single_column_by_index_from_csv(file_path, column_index):
    df = pd.read_csv(file_path, header=None, usecols=[column_index])
    return df[column_index]


def create_dataset(X, y, time_steps=1):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X[i:(i + time_steps)]
        Xs.append(v)
        ys.append(y[i + time_steps])
    return np.array(Xs), np.array(ys)


sampling_rate_opt = 800
sampling_rate_ref = 12800

ref = pd.read_csv(r"./datasets/242354_0009_ref.csv", header=None, usecols=[0])
df = pd.read_csv(r"./datasets/242354_0009_opt.csv", delim_whitespace=True, header=None)
col1 = np.array(df[0])
cw1 = np.mean(col1[50:100])
col2 = np.array(df[1])
cw2 = np.mean(col2[50:100])
opt = -(col1 - col2) + (cw1 - cw2)

opt = opt[(sampling_rate_opt*2):(sampling_rate_opt*2)+(sampling_rate_opt*8)]
ref = ref[(sampling_rate_ref*2):(sampling_rate_ref*2)+(sampling_rate_ref*8)]
print(len(opt))

interp_factor = int(sampling_rate_ref / sampling_rate_opt)

# Create an array for the new resampled dataset
resampled_ref = np.interp(
    np.linspace(0, len(ref) - 1, len(opt)),
    np.arange(len(ref)),
    ref.values.flatten()
)

n_samples = len(resampled_ref)
start_frequency = 10  # 10Hz
end_frequency = 200  # 200Hz
target_frequency = 50
frequencies = np.linspace(10, 200, n_samples)

step_size = (end_frequency - start_frequency) / (n_samples - 1)

# Calculate index of target frequency
target_index = int((target_frequency - start_frequency) / step_size)

# Get the wavelength at 50Hz
wavelength_at_50Hz = opt[target_index]
N = 10

# Assuming 'opt' contains wavelengths from the optical sensor
# and 'ref' contains measurements from the reference sensor
X = np.array(opt)  # Replace with optical sensor data
y = np.array(resampled_ref)  # Replace with reference sensor data

# Reshape to (samples, time_steps, features)
X_seq, y_seq = create_dataset(X, y, N)

# Reshape X_seq for LSTM
X_seq = X_seq.reshape((X_seq.shape[0], X_seq.shape[1], 1))

# Split data

# Assume X and y are your data
# Convert to PyTorch tensors
X_torch = torch.tensor(X_seq, dtype=torch.float32)
y_torch = torch.tensor(y_seq, dtype=torch.float32)

# Create DataLoader
train_data = TensorDataset(X_torch, y_torch)
train_loader = DataLoader(train_data, shuffle=True, batch_size=64)

# Initialize model, loss, optimizer
model = SimpleLSTM(input_dim=1, hidden_dim=50, output_dim=1).cuda()  # .cuda() for GPU
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(50):
    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.cuda(), batch_y.cuda()  # .cuda() for GPU
        optimizer.zero_grad()
        output = model(batch_X)
        loss = criterion(output, batch_y)
        loss.backward()
        optimizer.step()


# Predict sensitivity at 50Hz
print(target_index)
target_index = 3500
# Assume target_index calculated the same as in the previous examples
target_sequence = X[target_index : target_index + N]
target_sequence = target_sequence.reshape((1, N, 1))

# Predict sensitivity at 50Hz
input_data = target_sequence.cuda()

# Make predictions
with torch.no_grad():  # Deactivates autograd, reduces memory usage and speeds up computations
    predictions = model(input_data)

# If your output is on GPU and you want to bring it back to CPU for further analysis
predictions = predictions.cpu()

# Convert tensor to numpy array
predictions_array = predictions.numpy()
predicted_sensitivity_50Hz = model.predict(target_sequence)[0][0]

print(f"Predicted sensitivity at 50Hz: {predicted_sensitivity_50Hz}")

plt.figure()


opt_acc = opt*predicted_sensitivity_50Hz
# Plot the first data set
plt.plot(opt_acc, label='opt', linestyle='-', marker='o')

# Plot the second data set
plt.plot(resampled_ref, label='ref', linestyle='--', marker='x')

# Add title and labels
plt.xlabel('x-axis')
plt.ylabel('y-axis')
plt.title('Multiple Data Sets in One Plot')

# Add legend
plt.legend()

# Show the plot
plt.show()

