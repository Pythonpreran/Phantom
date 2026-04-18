"""
PHANTOM Module 2  --  Specialist Autoencoder
==========================================
32-dim input → 4-dim bottleneck → 32-dim reconstruction.
Trained only on benign events from one specific layer.
"""

import torch
import torch.nn as nn


class SpecialistAutoencoder(nn.Module):
    """
    32-dim input → 4-dim bottleneck → 32-dim reconstruction.
    Trained only on benign events from one specific layer.
    The 4-dim latent vector is the 'threat fingerprint' used by the Fusion Engine.
    """

    def __init__(self, input_dim: int = 32):
        super().__init__()
        self.input_dim = input_dim

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.GELU(),        # smoother than ReLU for anomaly detection
            nn.Dropout(0.1),   # regularization
            nn.Linear(16, 8),
            nn.GELU(),
            nn.Linear(8, 4),   # bottleneck: compressed threat fingerprint
        )

        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(8, 16),
            nn.GELU(),
            nn.Linear(16, input_dim),
            nn.Sigmoid(),      # output clamped to [0,1]  --  matches MinMax input
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the 4-dim bottleneck representation (latent vector)."""
        return self.encoder(x)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Reconstruct from latent representation."""
        return self.decoder(z)

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Returns per-sample MSE reconstruction error."""
        recon = self.forward(x)
        return ((x - recon) ** 2).mean(dim=1)

    def get_latent(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the 4-dim bottleneck representation."""
        return self.encoder(x)

    def anomaly_score(self, x: torch.Tensor, threshold: float) -> torch.Tensor:
        """Returns dimensionless anomaly score (recon_error / threshold)."""
        errors = self.reconstruction_error(x)
        return errors / threshold
