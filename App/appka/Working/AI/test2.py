import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim=1, num_layers=1):
        super(LSTMModel, self).__init__()

        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h_0 = torch.zeros(1, x.size(0), hidden_dim).to(x.device)
        c_0 = torch.zeros(1, x.size(0), hidden_dim).to(x.device)

        out, _ = self.lstm(x, (h_0, c_0))
        out = self.linear(out[:, -1, :])
        return out


# Generating synthetic data
# Here, `n_samples` should be replaced by the actual number of samples in your dataset
sampling_rate_opt = 800
sampling_rate_ref = 12800


def load_dataset(file):
    ref = pd.read_csv(fr"./datasets/{file}_ref.csv", header=None, usecols=[0])
    df = pd.read_csv(fr"./datasets/{file}_opt.csv", delim_whitespace=True, header=None)
    col1 = np.array(df[0])
    cw1 = np.mean(col1[50:100])
    col2 = np.array(df[1])
    cw2 = np.mean(col2[50:100])
    opt = -(col1 - col2) + (cw1 - cw2)

    opt = opt[(sampling_rate_opt*2):(sampling_rate_opt*2)+(sampling_rate_opt*8)]
    ref = ref[(sampling_rate_ref*2):(sampling_rate_ref*2)+(sampling_rate_ref*8)]

    interp_factor = int(sampling_rate_ref / sampling_rate_opt)

    # Create an array for the new resampled dataset
    resampled_ref = np.interp(
        np.linspace(0, len(ref) - 1, len(opt)),
        np.arange(len(ref)),
        ref.values.flatten()
    )
    return opt, resampled_ref


# Assume you have three datasets, you can add more
optical_sensor_data1, reference_sensor_data1 = load_dataset("242354_0009")
optical_sensor_data2, reference_sensor_data2 = load_dataset("242356_0008")
optical_sensor_data3, reference_sensor_data3 = load_dataset("242359_0001")
optical_sensor_data4, reference_sensor_data4 = load_dataset("246628_0001")
optical_sensor_data5, reference_sensor_data5 = load_dataset("246629_0001")

n_samples = len(reference_sensor_data4)

y1 = np.full((n_samples, 1), 1303.0333493747548)
y2 = np.full((n_samples, 1), 1327.683432759238)
y3 = np.full((n_samples, 1), 1352.2071746930385)
y4 = np.full((n_samples, 1), 1331.021035227017)
y5 = np.full((n_samples, 1), 1334.2387884059501)
y_all = np.concatenate([y1, y2, y3, y4, y5])

# Concatenate the datasets
reference_sensor_all = np.concatenate([reference_sensor_data1, reference_sensor_data2, reference_sensor_data3, reference_sensor_data4, reference_sensor_data5])
optical_sensor_all = np.concatenate([optical_sensor_data1, optical_sensor_data2, optical_sensor_data3, optical_sensor_data4, optical_sensor_data5])

# Proceed with scaling, splitting, and model training as before

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
train_data = torch.utils.data.TensorDataset(X_train, y_train)
train_loader = torch.utils.data.DataLoader(train_data, batch_size=32, shuffle=True)

# Initialize model, loss function and optimizer
model = LSTMModel(input_dim, hidden_dim).to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# Training loop
for epoch in range(num_epochs):
    for batch_X, batch_y in train_loader:
        outputs = model(batch_X.unsqueeze(1))
        loss = criterion(outputs, batch_y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

model_save_path = "./modely/model_sens_2ch"
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
optical_sensor_new, reference_sensor_new = load_dataset("246630_0001")

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

print(predicted_sensitivity_new_np)
