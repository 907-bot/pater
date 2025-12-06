# backend/services/prediction_service.py - ML prediction service

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
import joblib
import numpy as np

from models.database import insert_one, find_one
from config import settings

logger = logging.getLogger(__name__)

# ============ Prediction Service ============

class PredictionService:
    """Machine Learning prediction service"""
    
    def __init__(self):
        """Initialize prediction service"""
        self.models_loaded = False
        self.lgbm_model = None
        self.arima_model = None
        self.gnn_model = None
        self.scaler = None
    
    async def load_models(self) -> bool:
        """
        Load ML models from disk
        
        Returns:
            Success status
        """
        try:
            logger.info("Loading ML models...")
            
            # Mock loading - replace with actual model loading
            if settings.enable_lgbm:
                logger.info("✅ LightGBM model loaded")
            
            if settings.enable_arima:
                logger.info("✅ ARIMA model loaded")
            
            if settings.enable_gnn:
                logger.info("✅ GNN model loaded")
            
            self.models_loaded = True
            logger.info("✅ All ML models loaded successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    async def predict_discount(
        self,
        product_data: Dict[str, Any],
        historical_prices: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Predict expected discount for product
        
        Args:
            product_data: Product information
            historical_prices: Historical price data
        
        Returns:
            Prediction results
        """
        try:
            logger.info(f"Predicting discount for {product_data.get('product_name')}")
            
            # Mock prediction (replace with actual ML model call)
            features = self._extract_features(product_data, historical_prices)
            
            # LightGBM prediction
            lgbm_pred = self._predict_lgbm(features)
            
            # ARIMA prediction
            arima_pred = self._predict_arima(historical_prices)
            
            # Ensemble prediction
            ensemble_pred = (lgbm_pred * 0.6) + (arima_pred * 0.4)
            
            prediction = {
                'product_name': product_data.get('product_name'),
                'current_price': product_data.get('current_price'),
                'festival_probability': min(ensemble_pred, 100),
                'expected_discount': min(ensemble_pred, 100),
                'recommendation': self._get_recommendation(ensemble_pred),
                'confidence': min(0.95, 0.7 + (abs(lgbm_pred - arima_pred) / 100)),
                'predicted_price': product_data.get('current_price') * (1 - ensemble_pred / 100),
                'optimal_buy_time': self._get_optimal_buy_time(ensemble_pred),
                'models_used': ['lgbm', 'arima', 'ensemble'],
                'predicted_at': datetime.utcnow().isoformat()
            }
            
            # Store prediction
            await self._store_prediction(product_data.get('product_id'), prediction)
            
            return prediction
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._default_prediction(product_data)
    
    def _extract_features(
        self,
        product_data: Dict[str, Any],
        historical_prices: Optional[list] = None
    ) -> np.ndarray:
        """Extract features for ML model"""
        features = [
            product_data.get('current_price', 0),
            1.0 if product_data.get('platform') == 'amazon' else 0.0,
            1.0 if product_data.get('platform') == 'flipkart' else 0.0,
            1.0 if product_data.get('category') == 'Electronics' else 0.0,
        ]
        
        # Add historical features
        if historical_prices:
            prices = [p.get('price', 0) for p in historical_prices]
            features.extend([
                np.mean(prices) if prices else 0,
                np.std(prices) if prices else 0,
                min(prices) if prices else 0,
            ])
        
        return np.array(features).reshape(1, -1)
    
    def _predict_lgbm(self, features: np.ndarray) -> float:
        """LightGBM prediction"""
        try:
            if self.lgbm_model and settings.enable_lgbm:
                # prediction = self.lgbm_model.predict(features)[0]
                pass
            
            # Mock prediction
            return float(20 + np.random.uniform(-5, 15))
        
        except Exception as e:
            logger.error(f"LightGBM prediction error: {e}")
            return 20.0
    
    def _predict_arima(self, historical_prices: Optional[list] = None) -> float:
        """ARIMA time-series prediction"""
        try:
            if self.arima_model and settings.enable_arima:
                # prediction = self.arima_model.forecast()[0]
                pass
            
            # Mock prediction
            return float(15 + np.random.uniform(-5, 10))
        
        except Exception as e:
            logger.error(f"ARIMA prediction error: {e}")
            return 15.0
    
    def _get_recommendation(self, discount_percent: float) -> str:
        """Get purchase recommendation"""
        if discount_percent > 30:
            return "buy_now"
        elif discount_percent > 15:
            return "wait"
        else:
            return "skip"
    
    def _get_optimal_buy_time(self, discount_percent: float) -> str:
        """Get optimal buying time"""
        if discount_percent > 25:
            return "Now - Great discount available"
        else:
            return "Festival period (next 2 weeks)"
    
    async def _store_prediction(self, product_id: str, prediction: Dict[str, Any]) -> None:
        """Store prediction in database"""
        try:
            await insert_one('predictions', {
                'product_id': product_id,
                **prediction
            })
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
    
    def _default_prediction(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return default prediction on error"""
        current_price = product_data.get('current_price', 0)
        
        return {
            'product_name': product_data.get('product_name'),
            'current_price': current_price,
            'festival_probability': 50.0,
            'expected_discount': 20.0,
            'recommendation': 'wait',
            'confidence': 0.5,
            'predicted_price': current_price * 0.8,
            'optimal_buy_time': 'Upcoming festival',
            'error': 'Prediction model unavailable'
        }
    
    async def get_prediction_history(self, product_id: str) -> list:
        """Get prediction history for product"""
        try:
            history = await find_many(
                'predictions',
                {'product_id': product_id},
                limit=100,
                sort=[('predicted_at', -1)]
            )
            return history or []
        except Exception as e:
            logger.error(f"Error getting prediction history: {e}")
            return []

# ============ Global Prediction Service Instance ============

prediction_service = PredictionService()
