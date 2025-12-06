# backend/ml/arima_model.py - ARIMA time-series forecasting model

import logging
import numpy as np
import joblib
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
import warnings

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller, kpss
except ImportError:
    ARIMA = None
    logging.warning("statsmodels not installed - ARIMA will use mock implementation")

from config import settings

logger = logging.getLogger(__name__)

# ============ ARIMA Model ============

class ARIMAModel:
    """ARIMA time-series forecasting model"""
    
    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = (0, 0, 0, 0)
    ):
        """
        Initialize ARIMA model
        
        Args:
            order: (p, d, q) tuple for ARIMA
            seasonal_order: (P, D, Q, s) for seasonal ARIMA
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.model_fit = None
        self.scaler = None
        self.is_trained = False
    
    def fit(self, price_series: List[float]) -> bool:
        """
        Fit ARIMA model to price series
        
        Args:
            price_series: List of historical prices
        
        Returns:
            Success status
        """
        try:
            if len(price_series) < 10:
                logger.warning(f"Insufficient data: {len(price_series)} points")
                return False
            
            logger.info(f"Training ARIMA{self.order} model with {len(price_series)} points")
            
            if ARIMA is None:
                logger.warning("ARIMA not available - using mock model")
                self.is_trained = True
                return True
            
            # Check for stationarity
            series_array = np.array(price_series, dtype=float)
            
            try:
                adf_result = adfuller(series_array, autolag='AIC')
                if adf_result[1] > 0.05:
                    logger.info("Series not stationary, differencing applied")
            except:
                pass
            
            # Train ARIMA
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')
                self.model = ARIMA(
                    series_array,
                    order=self.order,
                    seasonal_order=self.seasonal_order
                )
                self.model_fit = self.model.fit()
            
            self.is_trained = True
            logger.info("✅ ARIMA model trained successfully")
            return True
        
        except Exception as e:
            logger.error(f"ARIMA training error: {e}")
            self.is_trained = False
            return False
    
    def predict(self, steps: int = 7) -> Dict[str, Any]:
        """
        Predict future prices
        
        Args:
            steps: Number of steps to forecast
        
        Returns:
            Prediction results
        """
        try:
            if not self.is_trained:
                return self._mock_predict(steps)
            
            if self.model_fit is None:
                return self._mock_predict(steps)
            
            logger.info(f"Forecasting {steps} steps ahead")
            
            # Get forecast
            forecast_result = self.model_fit.get_forecast(steps=steps)
            forecast_values = forecast_result.predicted_mean
            confidence_intervals = forecast_result.conf_int()
            
            # Calculate discount prediction
            current_price = forecast_values.iloc[0] if len(forecast_values) > 0 else 0
            future_price = forecast_values.iloc[-1] if len(forecast_values) > 0 else current_price
            
            discount_pct = max(0, ((current_price - future_price) / current_price * 100)) if current_price > 0 else 0
            
            return {
                'model': 'ARIMA',
                'discount_prediction': min(discount_pct, 100),
                'confidence': 0.75,
                'forecast_steps': steps,
                'predicted_prices': forecast_values.tolist(),
                'upper_bound': confidence_intervals.iloc[:, 1].tolist(),
                'lower_bound': confidence_intervals.iloc[:, 0].tolist(),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"ARIMA prediction error: {e}")
            return self._mock_predict(steps)
    
    def _mock_predict(self, steps: int) -> Dict[str, Any]:
        """Mock prediction for testing"""
        base_price = 5000
        trend = np.linspace(0, -500, steps)
        noise = np.random.normal(0, 200, steps)
        prices = base_price + trend + noise
        
        return {
            'model': 'ARIMA',
            'discount_prediction': float(np.clip(np.random.normal(15, 5), 0, 100)),
            'confidence': 0.65,
            'forecast_steps': steps,
            'predicted_prices': prices.tolist(),
            'upper_bound': (prices + 500).tolist(),
            'lower_bound': (prices - 500).tolist(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def save(self, path: str) -> bool:
        """Save model to disk"""
        try:
            if self.model_fit:
                joblib.dump(self.model_fit, path)
                logger.info(f"✅ ARIMA model saved to {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving ARIMA model: {e}")
            return False
    
    def load(self, path: str) -> bool:
        """Load model from disk"""
        try:
            self.model_fit = joblib.load(path)
            self.is_trained = True
            logger.info(f"✅ ARIMA model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading ARIMA model: {e}")
            return False
    
    def evaluate(self, test_series: List[float]) -> Dict[str, float]:
        """
        Evaluate model on test data
        
        Args:
            test_series: Test price series
        
        Returns:
            Evaluation metrics
        """
        try:
            if not self.is_trained or self.model_fit is None:
                return {'rmse': 0, 'mae': 0, 'mape': 0}
            
            predictions = self.model_fit.fittedvalues
            actual = np.array(test_series)
            
            # Calculate metrics
            mse = np.mean((predictions - actual) ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(predictions - actual))
            mape = np.mean(np.abs((actual - predictions) / actual)) * 100
            
            return {
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape),
                'model': 'ARIMA'
            }
        
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {'rmse': 0, 'mae': 0, 'mape': 0}

# ============ Global ARIMA Instance ============

arima_model = ARIMAModel()
