"""
PHANTOM  --  Pretrained Model Builder
====================================
Trains all 3 specialist autoencoders on synthetic benign data.
Saves .pt files, scaler.pkl, and thresholds.json.

Run ONCE before the demo  --  no training during live presentation.
"""

import os
import sys
import json
import pickle

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.autoencoder import SpecialistAutoencoder
from data.generate_synthetic import generate_training_data


def train_single_autoencoder(
    layer_name: str,
    train_data: np.ndarray,
    val_data: np.ndarray,
    save_dir: str = "models",
    epochs: int = 80,
    patience: int = 10,
    batch_size: int = 64,
    lr: float = 1e-3,
) -> tuple:
    """
    Train one specialist autoencoder on benign data.
    Returns (model, threshold).
    """
    print(f"\n{'='*60}")
    print(f"  Training Guard: {layer_name.upper()}")
    print(f"  Train samples: {len(train_data)} | Val samples: {len(val_data)}")
    print(f"{'='*60}")

    # Create data loaders
    train_tensor = torch.tensor(train_data, dtype=torch.float32)
    val_tensor = torch.tensor(val_data, dtype=torch.float32)

    train_loader = DataLoader(
        TensorDataset(train_tensor), batch_size=batch_size, shuffle=True
    )
    val_loader = DataLoader(
        TensorDataset(val_tensor), batch_size=batch_size, shuffle=False
    )

    # Initialize model
    model = SpecialistAutoencoder(input_dim=32)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    criterion = nn.MSELoss()

    best_val_loss = float("inf")
    patience_counter = 0
    best_state = None

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        for (batch,) in train_loader:
            optimizer.zero_grad()
            recon = model(batch)
            loss = criterion(recon, batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for (batch,) in val_loader:
                recon = model(batch)
                loss = criterion(recon, batch)
                val_loss += loss.item()
        val_loss /= len(val_loader)
        scheduler.step(val_loss)

        if epoch % 10 == 0 or epoch == epochs - 1:
            print(f"  Epoch {epoch:3d}/{epochs} | Train: {train_loss:.6f} | Val: {val_loss:.6f}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = model.state_dict().copy()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  [STOP] Early stopping at epoch {epoch}")
                break

    # Load best model
    model.load_state_dict(best_state)

    # Save model weights
    model_path = os.path.join(save_dir, f"ae_{layer_name}.pt")
    torch.save(model.state_dict(), model_path)
    print(f"  [OK] Model saved: {model_path}")

    # Compute threshold: mu + 3sigma on benign validation set
    model.eval()
    errors = []
    with torch.no_grad():
        for (batch,) in val_loader:
            errs = model.reconstruction_error(batch)
            errors.extend(errs.numpy().tolist())

    mu = np.mean(errors)
    sigma = np.std(errors)
    threshold = mu + 3 * sigma
    print(f"  [STAT] Threshold: {threshold:.6f} (mu={mu:.6f}, sigma={sigma:.6f})")

    return model, threshold


def train_all():
    """
    Full training pipeline:
    1. Generate synthetic data
    2. Fit MinMaxScaler on benign data
    3. Train 3 specialist autoencoders
    4. Save all artifacts (.pt, scaler.pkl, thresholds.json)
    """
    print("\n" + "=" * 60)
    print("  PHANTOM  --  Pretrained Model Builder")
    print("  Building specialist guards...")
    print("=" * 60)

    # Step 1: Generate synthetic data
    all_benign, all_attacks = generate_training_data(
        output_dir=os.path.join(os.path.dirname(__file__), "..", "data")
    )

    save_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(save_dir, exist_ok=True)

    # Step 2: Fit global scaler on ALL benign data
    print("\n[PHANTOM] Fitting MinMaxScaler on benign data...")
    all_benign_vectors = []
    for layer in ["network", "application", "endpoint"]:
        all_benign_vectors.extend(all_benign[layer])

    all_benign_matrix = np.array(all_benign_vectors, dtype=np.float32)
    scaler = MinMaxScaler()
    scaler.fit(all_benign_matrix)

    scaler_path = os.path.join(save_dir, "scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  [OK] Scaler saved: {scaler_path}")

    # Step 3: Train each specialist autoencoder
    thresholds = {}

    for layer_name in ["network", "application", "endpoint"]:
        # Scale benign data
        benign_raw = np.array(all_benign[layer_name], dtype=np.float32)
        benign_scaled = scaler.transform(benign_raw)

        # 80/20 train/val split
        split_idx = int(len(benign_scaled) * 0.8)
        train_data = benign_scaled[:split_idx]
        val_data = benign_scaled[split_idx:]

        model, threshold = train_single_autoencoder(
            layer_name=layer_name,
            train_data=train_data,
            val_data=val_data,
            save_dir=save_dir,
            epochs=80,
            patience=10,
        )

        thresholds[layer_name] = float(threshold)

    # Step 4: Save thresholds
    thresholds_path = os.path.join(save_dir, "thresholds.json")
    with open(thresholds_path, "w") as f:
        json.dump(thresholds, f, indent=2)
    print(f"\n  [OK] Thresholds saved: {thresholds_path}")
    print(f"     {json.dumps(thresholds, indent=2)}")

    print("\n" + "=" * 60)
    print("  [OK] ALL GUARDS TRAINED  --  Ready for Demo")
    print("  Models: ae_network.pt, ae_application.pt, ae_endpoint.pt")
    print("  Scaler: scaler.pkl | Thresholds: thresholds.json")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    train_all()
