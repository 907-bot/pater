# backend/ml/utils.py - ML utility functions

import logging
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# ============ Normalization Functions ============

def normalize_features(
    features: np.ndarray,
    scaler: Optional[StandardScaler] = None,
    method: str = 'standard'
) -> Tuple[np.ndarray, StandardScaler]:
    """
    Normalize features
    
    Args:
        features: Input features
        scaler: Fitted scaler (optional)
        method: 'standard' or 'minmax'
    
    Returns:
        Normalized features and scaler
    """
    try:
        if scaler is None:
            if method == 'standard':
                scaler = StandardScaler()
            else:
                scaler = MinMaxScaler()
            normalized = scaler.fit_transform(features)
        else:
            normalized = scaler.transform(features)
        
        logger.debug(f"Features normalized using {method} method")
        return normalized, scaler
    
    except Exception as e:
        logger.error(f"Normalization error: {e}")
        return features, scaler

def denormalize_features(
    normalized_features: np.ndarray,
    scaler: StandardScaler
) -> np.ndarray:
    """
    Denormalize features
    
    Args:
        normalized_features: Normalized features
        scaler: Fitted scaler
    
    Returns:
        Original scale features
    """
    try:
        denormalized = scaler.inverse_transform(normalized_features)
        logger.debug("Features denormalized")
        return denormalized
    except Exception as e:
        logger.error(f"Denormalization error: {e}")
        return normalized_features

# ============ Feature Engineering ============

def extract_price_features(price_series: List[float]) -> Dict[str, float]:
    """
    Extract statistical features from price series
    
    Args:
        price_series: Historical prices
    
    Returns:
        Feature dictionary
    """
    try:
        if len(price_series) == 0:
            return {}
        
        prices = np.array(price_series, dtype=float)
        
        features = {
            'mean_price': float(np.mean(prices)),
            'std_price': float(np.std(prices)),
            'min_price': float(np.min(prices)),
            'max_price': float(np.max(prices)),
            'median_price': float(np.median(prices)),
            'range_price': float(np.max(prices) - np.min(prices)),
            'current_price': float(prices[-1]),
            'price_trend': float(np.polyfit(np.arange(len(prices)), prices, 1)[0]),
            'volatility': float(np.std(np.diff(prices))),
            'momentum': float(prices[-1] - prices[0]) if len(prices) > 1 else 0.0
        }
        
        return features
    
    except Exception as e:
        logger.error(f"Feature extraction error: {e}")
        return {}

def create_lagged_features(
    series: List[float],
    lags: int = 7
) -> np.ndarray:
    """
    Create lagged features for time-series
    
    Args:
        series: Input series
        lags: Number of lags
    
    Returns:
        Lagged features array
    """
    try:
        if len(series) < lags:
            logger.warning(f"Series too short for {lags} lags")
            return np.array([])
        
        lagged = []
        for i in range(lags, len(series)):
            lagged.append(series[i-lags:i])
        
        return np.array(lagged)
    
    except Exception as e:
        logger.error(f"Lagged feature creation error: {e}")
        return np.array([])

# ============ Data Splitting ============

def split_train_test(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42,
    time_series: bool = False
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into train and test sets
    
    Args:
        X: Features
        y: Targets
        test_size: Test set fraction
        random_state: Random seed
        time_series: Use time-series split
    
    Returns:
        X_train, X_test, y_train, y_test
    """
    try:
        if time_series:
            # Time-series split (no shuffling)
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
        else:
            # Regular split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=test_size,
                random_state=random_state
            )
        
        logger.info(f"Data split: {len(X_train)} train, {len(X_test)} test")
        return X_train, X_test, y_train, y_test
    
    except Exception as e:
        logger.error(f"Data split error: {e}")
        return X, X, y, y

# ============ Evaluation Metrics ============

def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Calculate evaluation metrics
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        Metrics dictionary
    """
    try:
        y_true = np.array(y_true, dtype=float)
        y_pred = np.array(y_pred, dtype=float)
        
        # Regression metrics
        mse = np.mean((y_true - y_pred) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_true - y_pred))
        
        # MAPE
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(np.abs(y_true), 1))) * 100
        
        # R² Score
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Correlation
        if len(y_true) > 1:
            correlation = np.corrcoef(y_true, y_pred)[0, 1]
        else:
            correlation = 0
        
        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape),
            'r2': float(r2),
            'correlation': float(correlation)
        }
        
        logger.info(f"Metrics - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")
        return metrics
    
    except Exception as e:
        logger.error(f"Metrics calculation error: {e}")
        return {}

# ============ Data Validation ============

def validate_data(
    X: np.ndarray,
    y: np.ndarray
) -> Tuple[bool, str]:
    """
    Validate training data
    
    Args:
        X: Features
        y: Targets
    
    Returns:
        (is_valid, message)
    """
    try:
        # Check shapes
        if len(X) != len(y):
            return False, "Feature and target lengths don't match"
        
        # Check minimum samples
        if len(X) < 5:
            return False, "Insufficient samples (minimum 5)"
        
        # Check for NaN/Inf
        if np.any(np.isnan(X)) or np.any(np.isinf(X)):
            return False, "Features contain NaN or Inf"
        
        if np.any(np.isnan(y)) or np.any(np.isinf(y)):
            return False, "Targets contain NaN or Inf"
        
        # Check dimensionality
        if len(X.shape) != 2:
            return False, "Features must be 2D array"
        
        if len(y.shape) != 1:
            return False, "Targets must be 1D array"
        
        return True, "Data is valid"
    
    except Exception as e:
        return False, str(e)

# ============ Model Selection ============

def get_best_hyperparameters(
    model_name: str,
    dataset_size: int
) -> Dict[str, Any]:
    """
    Get recommended hyperparameters based on dataset size
    
    Args:
        model_name: Model name (arima, lgbm, gnn)
        dataset_size: Number of training samples
    
    Returns:
        Recommended hyperparameters
    """
    if model_name == 'arima':
        return {
            'order': (1, 1, 1),
            'seasonal_order': (0, 0, 0, 0)
        }
    
    elif model_name == 'lgbm':
        if dataset_size < 100:
            return {'num_leaves': 15, 'learning_rate': 0.1, 'n_estimators': 50}
        elif dataset_size < 1000:
            return {'num_leaves': 31, 'learning_rate': 0.05, 'n_estimators': 100}
        else:
            return {'num_leaves': 63, 'learning_rate': 0.02, 'n_estimators': 200}
    
    elif model_name == 'gnn':
        return {
            'input_dim': 10,
            'hidden_dim': 32,
            'output_dim': 1,
            'num_layers': 2
        }
    
    return {}
