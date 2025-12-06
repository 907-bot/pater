# backend/ml/lgbm_model.py - LightGBM gradient boosting model

import logging
import numpy as np
import joblib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

try:
    import lightgbm as lgb
    from sklearn.preprocessing import StandardScaler
except ImportError:
    lgb = None
    logging.warning("lightgbm not installed - LGBMModel will use mock implementation")

from config import settings

logger = logging.getLogger(__name__)

# ============ LightGBM Model ============

class LGBMModel:
    """LightGBM gradient boosting regression model"""
    
    def __init__(
        self,
        num_leaves: int = 31,
        learning_rate: float = 0.05,
        n_estimators: int = 100
    ):
        """
        Initialize LightGBM model
        
        Args:
            num_leaves: Number of leaves in trees
            learning_rate: Learning rate
            n_estimators: Number of boosting rounds
        """
        self.num_leaves = num_leaves
        self.learning_rate = learning_rate
        self.n_estimators = n_estimators
        self.model = None
        self.scaler = StandardScaler() if lgb else None
        self.is_trained = False
        self.feature_names = None
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> bool:
        """
        Train LightGBM model
        
        Args:
            X_train: Training features (n_samples, n_features)
            y_train: Training targets
            feature_names: Feature names
        
        Returns:
            Success status
        """
        try:
            if len(X_train) < 10:
                logger.warning(f"Insufficient training data: {len(X_train)} samples")
                return False
            
            logger.info(f"Training LightGBM with {len(X_train)} samples, {X_train.shape[1]} features")
            
            if lgb is None:
                logger.warning("LightGBM not available - using mock model")
                self.is_trained = True
                self.feature_names = feature_names or [f"feature_{i}" for i in range(X_train.shape[1])]
                return True
            
            # Normalize features
            X_normalized = self.scaler.fit_transform(X_train)
            
            # Create dataset
            train_data = lgb.Dataset(
                X_normalized,
                label=y_train,
                feature_name=feature_names or [f"feature_{i}" for i in range(X_train.shape[1])]
            )
            
            # Train model
            self.model = lgb.train(
                params={
                    'objective': 'regression',
                    'metric': 'rmse',
                    'num_leaves': self.num_leaves,
                    'learning_rate': self.learning_rate,
                    'verbose': -1
                },
                train_set=train_data,
                num_boost_round=self.n_estimators,
                callbacks=[lgb.log_evaluation(period=0)]
            )
            
            self.feature_names = feature_names or [f"feature_{i}" for i in range(X_train.shape[1])]
            self.is_trained = True
            logger.info("✅ LightGBM model trained successfully")
            return True
        
        except Exception as e:
            logger.error(f"LightGBM training error: {e}")
            self.is_trained = False
            return False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions
        
        Args:
            X: Features to predict on
        
        Returns:
            Predicted discount percentages
        """
        try:
            if not self.is_trained:
                return self._mock_predict(X)
            
            if lgb is None or self.model is None:
                return self._mock_predict(X)
            
            # Normalize features
            X_normalized = self.scaler.transform(X)
            
            # Predict
            predictions = self.model.predict(X_normalized)
            
            # Clip to valid range (0-100%)
            predictions = np.clip(predictions, 0, 100)
            
            return predictions
        
        except Exception as e:
            logger.error(f"LightGBM prediction error: {e}")
            return self._mock_predict(X)
    
    def _mock_predict(self, X: np.ndarray) -> np.ndarray:
        """Mock predictions for testing"""
        n_samples = X.shape[0] if len(X.shape) > 1 else 1
        base_discount = 20
        variation = np.random.normal(0, 8, n_samples)
        predictions = np.clip(base_discount + variation, 0, 100)
        return predictions
    
    def predict_with_confidence(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Make predictions with confidence estimates
        
        Args:
            X: Features
        
        Returns:
            Predictions and confidence scores
        """
        try:
            predictions = self.predict(X)
            
            # Estimate confidence based on feature values
            feature_variance = np.std(X, axis=0) if len(X.shape) > 1 else np.array([0])
            confidence = 0.9 - (np.mean(feature_variance) / 1000)  # Rough estimate
            confidence = np.clip(confidence, 0.5, 0.95)
            
            return {
                'predictions': predictions.tolist() if hasattr(predictions, 'tolist') else list(predictions),
                'confidence': float(confidence),
                'model': 'LightGBM',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Prediction with confidence error: {e}")
            return {
                'predictions': [],
                'confidence': 0.0,
                'model': 'LightGBM',
                'error': str(e)
            }
    
    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """
        Get feature importance scores
        
        Args:
            top_n: Top N features to return
        
        Returns:
            Feature importance dictionary
        """
        try:
            if not self.is_trained or self.model is None:
                return {}
            
            importance = self.model.feature_importance()
            feature_names = self.feature_names or [f"feature_{i}" for i in range(len(importance))]
            
            # Sort by importance
            sorted_idx = np.argsort(importance)[::-1][:top_n]
            
            importance_dict = {
                feature_names[i]: float(importance[i])
                for i in sorted_idx
            }
            
            return importance_dict
        
        except Exception as e:
            logger.error(f"Feature importance error: {e}")
            return {}
    
    def save(self, path: str) -> bool:
        """Save model to disk"""
        try:
            if self.model:
                self.model.save_model(path)
                logger.info(f"✅ LightGBM model saved to {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving LightGBM model: {e}")
            return False
    
    def load(self, path: str) -> bool:
        """Load model from disk"""
        try:
            if lgb is None:
                return False
            
            self.model = lgb.Booster(model_file=path)
            self.is_trained = True
            logger.info(f"✅ LightGBM model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading LightGBM model: {e}")
            return False
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model on test data
        
        Args:
            X_test: Test features
            y_test: Test targets
        
        Returns:
            Evaluation metrics
        """
        try:
            predictions = self.predict(X_test)
            
            # Calculate metrics
            mse = np.mean((predictions - y_test) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(predictions - y_test))
            mape = np.mean(np.abs((y_test - predictions) / np.maximum(y_test, 1))) * 100
            r2 = 1 - (np.sum((y_test - predictions) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
            
            return {
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape),
                'r2': float(r2),
                'model': 'LightGBM'
            }
        
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {'rmse': 0, 'mae': 0, 'mape': 0, 'r2': 0}

# ============ Global LightGBM Instance ============

lgbm_model = LGBMModel()
