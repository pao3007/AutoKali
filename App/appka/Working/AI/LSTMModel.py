import torch
import torch.nn as nn


class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim=1, num_layers=1, dropout_prob=0.5):
        super(LSTMModel, self).__init__()

        # Conv1D Layer
        self.conv1 = nn.Conv1d(input_dim, input_dim, kernel_size=3, padding=1)
        self.relu = nn.ReLU()

        # LSTM Layer
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True,
                            dropout=dropout_prob if num_layers > 1 else 0)

        # Dropout Layer
        self.dropout = nn.Dropout(dropout_prob)

        # Fully Connected Layers
        self.fc1 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc2 = nn.Linear(hidden_dim // 2, hidden_dim // 4)

        # Output Layer
        self.linear = nn.Linear(hidden_dim // 4, output_dim)

        self.hidden_dim = hidden_dim

    def forward(self, x):
        # Input shape for Conv1D: (batch_size, channels, length_of_sequence)
        # Ensuring input to Conv1D is correctly shaped
        print("Original shape:", x.shape)
        x = x.permute(0, 2, 1)
        print("Shape after transpose for Conv1d:", x.shape)

        # Conv1D and ReLU Activation
        x = self.conv1(x)
        x = self.relu(x)

        # Transpose back to match LSTM's input shape: (batch, seq_len, features)
        x = x.transpose(1, 2)
        print("Shape after transpose for LSTM:", x.shape)

        # Initialize hidden state and cell state
        h_0 = torch.zeros(self.lstm.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c_0 = torch.zeros(self.lstm.num_layers, x.size(0), self.hidden_dim).to(x.device)

        # LSTM
        out, _ = self.lstm(x, (h_0, c_0))

        # Dropout and Fully Connected Layers
        out = self.dropout(out[:, -1, :])  # Taking the output of the last time step
        out = self.fc1(out)
        out = self.fc2(out)

        # Output Layer
        out = self.linear(out)

        return out
