import os
import re
import joblib
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from LSTMModel import LSTMModel


# Generating synthetic data
# Here, `n_samples` should be replaced by the actual number of samples in your dataset
sampling_rate_opt = 800
sampling_rate_ref = 12800


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


# Get all the dataset names from a folder
folder_path = "./datasets"  # Change this to your datasets folder path
dataset_names = [f[:-8] for f in os.listdir(folder_path) if f.endswith('_opt.csv')]  # Filter and trim filenames

reference_sensor_all = None
optical_sensor_all = None
y_all = None

# Loop through the dataset names and load each one
for idx, name in enumerate(dataset_names):
    optical_sensor_data, reference_sensor_data, y_value = load_dataset(name)
    n_samples = len(reference_sensor_data)

    # Generate y data based on some calculation (replace the number with your own logic)
    y = optical_sensor_data/(y_value/1000)

    # Concatenate y values
    y_all = np.concatenate([y_all, y]) if y_all is not None else y

    # Concatenate reference_sensor_data
    reference_sensor_all = np.concatenate([reference_sensor_all, reference_sensor_data]) if reference_sensor_all is not None else reference_sensor_data

    # Concatenate optical_sensor_data
    optical_sensor_all = np.concatenate([optical_sensor_all, optical_sensor_data]) if optical_sensor_all is not None else optical_sensor_data
    print(name, " , ", y_value)

# Proceed with scaling, splitting, and model training as before
# print(y_all)
# Scale the data between 0 and 1
scaler = MinMaxScaler(feature_range=(0, 1))
reference_sensor_all = scaler.fit_transform(reference_sensor_all.reshape(-1, 1))
optical_sensor_all = scaler.fit_transform(optical_sensor_all.reshape(-1, 1))

# Prepare data for LSTM model
X_all = np.hstack((reference_sensor_all, optical_sensor_all))


# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.2, random_state=42)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

X_train = torch.FloatTensor(X_train).to(device)
X_test = torch.FloatTensor(X_test).to(device)
y_train = torch.FloatTensor(y_train).to(device)
y_test = torch.FloatTensor(y_test).to(device)

# The rest of the code for model definition and training remains largely the same.

# Hyperparameters
input_dim = 2  # Number of features (reference and optical sensor data)
hidden_dim = 50
output_dim = 1
num_epochs = 100
learning_rate = 0.001

# Create DataLoader objects

# Create DataLoader objects
X_train_unsqueezed = X_train.unsqueeze(1)  # Shape becomes [batch_size, 1, sequence_length]
X_test_unsqueezed = X_test.unsqueeze(1)  # Shape becomes [batch_size, 1, sequence_length]

train_data = torch.utils.data.TensorDataset(X_train_unsqueezed, y_train)
train_loader = torch.utils.data.DataLoader(train_data, batch_size=32, shuffle=True)

val_dataset = torch.utils.data.TensorDataset(X_test_unsqueezed, y_test)
val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32)

# Initialize model, loss function and optimizer
model = LSTMModel(input_dim, hidden_dim).to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)
best_val_loss = float('inf')

# Training loop
for epoch in range(num_epochs):
    model.train()
    train_loss = 0
    for batch_X, batch_y in train_loader:
        batch_X = batch_X.permute(0, 2, 1)
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X = batch_X.permute(0, 2, 1)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            val_loss += loss.item()

    train_loss /= len(train_loader)
    val_loss /= len(val_loader)

    print(f"Epoch {epoch+1}, Train Loss: {train_loss}, Val Loss: {val_loss}")

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), 'best_model.pth')
    else:
        print("Early stopping due to increase in validation loss")
        break

model_save_path = "./modely/model_sens_2ch_2"
torch.save(model.state_dict(), model_save_path)

model.eval()

# Calculate predictions on the test set
with torch.no_grad():
    X_test_unsqueezed = X_test.unsqueeze(1)  # Add the sequence length dimension
    predictions = model(X_test_unsqueezed).cpu()  # Get predictions and move to CPU

test_loss = criterion(predictions, y_test.cpu()).item()
mae = torch.mean(torch.abs(predictions - y_test.cpu())).item()
mse = torch.mean((predictions - y_test.cpu()) ** 2).item()
rmse = np.sqrt(mse)

print(f"Test Loss: {test_loss:.4f}")
print(f"Mean Absolute Error: {mae:.4f}")
print(f"Mean Squared Error: {mse:.4f}")
print(f"Root Mean Squared Error: {rmse:.4f}")

# Assume you have a new dataset
optical_sensor_new, reference_sensor_new, sens = load_dataset("242352_0011", diff_folder="added")

# You should use the same scaler object that you used for your training data to transform your new data.
# DO NOT fit the scaler again. Use the same scaler to transform (i.e., only use `transform` method)
reference_sensor_new_scaled = scaler.transform(reference_sensor_new.reshape(-1, 1))
optical_sensor_new_scaled = scaler.transform(optical_sensor_new.reshape(-1, 1))

# Prepare new data for LSTM model
X_new = np.hstack((reference_sensor_new_scaled, optical_sensor_new_scaled))

# Convert to PyTorch tensor and move to device
X_new_tensor = torch.FloatTensor(X_new).to(device).unsqueeze(1)

# Make sure the model is in evaluation mode
model.eval()

# Make predictions on new data
with torch.no_grad():
    predicted_sensitivity_new = model(X_new_tensor).cpu()

# Convert predictions to numpy array
predicted_sensitivity_new_np = predicted_sensitivity_new.numpy()

predicted_sensitivity_one_value = optical_sensor_new[3500]/predicted_sensitivity_new_np[3500]
predicted_sensitivity_two_value = predicted_sensitivity_new_np[3500]/optical_sensor_new[3500]

print(predicted_sensitivity_one_value, " / ", sens)
print(predicted_sensitivity_two_value, " / ", sens)

joblib.dump(scaler, 'scaler.pkl')
