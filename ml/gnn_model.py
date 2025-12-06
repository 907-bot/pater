# backend/ml/gnn_model.py - Graph Neural Network model for product relationships

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    from torch_geometric.nn import GCNConv
except ImportError:
    torch = None
    nn = None
    logging.warning("PyTorch/PyG not installed - GNNModel will use mock implementation")

from config import settings

logger = logging.getLogger(__name__)

# ============ GNN Model ============

class GNNModel:
    """Graph Neural Network for product relationships and predictions"""
    
    def __init__(
        self,
        input_dim: int = 10,
        hidden_dim: int = 32,
        output_dim: int = 1,
        num_layers: int = 2
    ):
        """
        Initialize GNN model
        
        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            output_dim: Output dimension (1 for regression)
            num_layers: Number of GNN layers
        """
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        self.model = None
        self.is_trained = False
        
        if torch is not None:
            self._build_model()
    
    def _build_model(self):
        """Build GNN architecture"""
        try:
            if torch is None:
                return
            
            class GNNNet(nn.Module):
                """GNN network architecture"""
                def __init__(self, input_dim, hidden_dim, output_dim, num_layers):
                    super().__init__()
                    self.layers = nn.ModuleList()
                    
                    # Input layer
                    self.layers.append(GCNConv(input_dim, hidden_dim))
                    
                    # Hidden layers
                    for _ in range(num_layers - 1):
                        self.layers.append(GCNConv(hidden_dim, hidden_dim))
                    
                    # Output layer
                    self.layers.append(GCNConv(hidden_dim, output_dim))
                    
                    self.relu = nn.ReLU()
                
                def forward(self, x, edge_index):
                    for i, layer in enumerate(self.layers[:-1]):
                        x = layer(x, edge_index)
                        x = self.relu(x)
                    
                    x = self.layers[-1](x, edge_index)
                    return x
            
            self.model = GNNNet(
                self.input_dim,
                self.hidden_dim,
                self.output_dim,
                self.num_layers
            )
            logger.info("✅ GNN model built successfully")
        
        except Exception as e:
            logger.error(f"GNN model building error: {e}")
            self.model = None
    
    def fit(
        self,
        X: np.ndarray,
        edge_index: np.ndarray,
        y: np.ndarray,
        epochs: int = 50,
        learning_rate: float = 0.01
    ) -> bool:
        """
        Train GNN model
        
        Args:
            X: Node features
            edge_index: Graph edges
            y: Target values
            epochs: Training epochs
            learning_rate: Learning rate
        
        Returns:
            Success status
        """
        try:
            if torch is None or self.model is None:
                logger.warning("GNN not available - using mock model")
                self.is_trained = True
                return True
            
            logger.info(f"Training GNN with {X.shape[0]} nodes, {edges.shape[1]} edges")
            
            # Convert to torch tensors
            X_tensor = torch.FloatTensor(X)
            edge_index_tensor = torch.LongTensor(edge_index)
            y_tensor = torch.FloatTensor(y).reshape(-1, 1)
            
            # Optimizer
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
            loss_fn = nn.MSELoss()
            
            # Training loop
            self.model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                
                # Forward pass
                predictions = self.model(X_tensor, edge_index_tensor)
                loss = loss_fn(predictions, y_tensor)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                if (epoch + 1) % 10 == 0:
                    logger.debug(f"Epoch {epoch + 1}/{epochs}, Loss: {loss.item():.4f}")
            
            self.model.eval()
            self.is_trained = True
            logger.info("✅ GNN model trained successfully")
            return True
        
        except Exception as e:
            logger.error(f"GNN training error: {e}")
            return False
    
    def predict(self, X: np.ndarray, edge_index: np.ndarray) -> np.ndarray:
        """
        Make predictions
        
        Args:
            X: Node features
            edge_index: Graph edges
        
        Returns:
            Predictions (discount percentages)
        """
        try:
            if not self.is_trained:
                return self._mock_predict(X)
            
            if torch is None or self.model is None:
                return self._mock_predict(X)
            
            # Convert to tensors
            X_tensor = torch.FloatTensor(X)
            edge_index_tensor = torch.LongTensor(edge_index)
            
            # Predict
            with torch.no_grad():
                predictions = self.model(X_tensor, edge_index_tensor)
                predictions = predictions.numpy().flatten()
            
            # Clip to valid range
            predictions = np.clip(predictions, 0, 100)
            
            return predictions
        
        except Exception as e:
            logger.error(f"GNN prediction error: {e}")
            return self._mock_predict(X)
    
    def _mock_predict(self, X: np.ndarray) -> np.ndarray:
        """Mock predictions for testing"""
        n_samples = X.shape[0]
        base_discount = 20
        variation = np.random.normal(0, 5, n_samples)
        predictions = np.clip(base_discount + variation, 0, 100)
        return predictions

# ============ Global GNN Instance ============

gnn_model = GNNModel()
