# backend/ml/ensemble.py - Ensemble predictor combining multiple models

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from .arima_model import arima_model
from .lgbm_model import lgbm_model
from .gnn_model import gnn_model

logger = logging.getLogger(__name__)

# ============ Ensemble Predictor ============

class EnsemblePredictor:
    """Ensemble predictor combining ARIMA, LightGBM, and GNN models"""
    
    def __init__(
        self,
        arima_weight: float = 0.3,
        lgbm_weight: float = 0.5,
        gnn_weight: float = 0.2
    ):
        """
        Initialize ensemble predictor
        
        Args:
            arima_weight: Weight for ARIMA predictions
            lgbm_weight: Weight for LightGBM predictions
            gnn_weight: Weight for GNN predictions
        """
        # Normalize weights
        total_weight = arima_weight + lgbm_weight + gnn_weight
        self.arima_weight = arima_weight / total_weight
        self.lgbm_weight = lgbm_weight / total_weight
        self.gnn_weight = gnn_weight / total_weight
        
        self.arima_model = arima_model
        self.lgbm_model = lgbm_model
        self.gnn_model = gnn_model
        
        logger.info(f"Ensemble weights - ARIMA: {self.arima_weight:.2f}, LightGBM: {self.lgbm_weight:.2f}, GNN: {self.gnn_weight:.2f}")
    
    def predict_discount(
        self,
        price_history: Optional[List[float]] = None,
        features: Optional[np.ndarray] = None,
        graph_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict discount using ensemble of models
        
        Args:
            price_history: Historical prices for ARIMA
            features: Features for LightGBM
            graph_data: Graph data for GNN (nodes and edges)
        
        Returns:
            Ensemble prediction results
        """
        try:
            predictions = {}
            confidence_scores = []
            
            # ARIMA prediction (time-series)
            if price_history and len(price_history) >= 5:
                try:
                    arima_result = self.arima_model.predict(steps=7)
                    arima_pred = arima_result.get('discount_prediction', 0)
                    predictions['arima'] = arima_pred
                    confidence_scores.append((self.arima_weight, arima_result.get('confidence', 0.5)))
                    logger.debug(f"ARIMA prediction: {arima_pred:.1f}%")
                except Exception as e:
                    logger.warning(f"ARIMA prediction failed: {e}")
                    predictions['arima'] = 0
            
            # LightGBM prediction (features)
            if features is not None:
                try:
                    if isinstance(features, list):
                        features = np.array(features).reshape(1, -1)
                    elif len(features.shape) == 1:
                        features = features.reshape(1, -1)
                    
                    lgbm_result = self.lgbm_model.predict_with_confidence(features)
                    lgbm_pred = lgbm_result['predictions'][0] if lgbm_result['predictions'] else 0
                    predictions['lgbm'] = lgbm_pred
                    confidence_scores.append((self.lgbm_weight, lgbm_result.get('confidence', 0.5)))
                    logger.debug(f"LightGBM prediction: {lgbm_pred:.1f}%")
                except Exception as e:
                    logger.warning(f"LightGBM prediction failed: {e}")
                    predictions['lgbm'] = 0
            
            # GNN prediction (graph-based)
            if graph_data:
                try:
                    node_features = graph_data.get('node_features')
                    edge_index = graph_data.get('edge_index')
                    
                    if node_features is not None and edge_index is not None:
                        gnn_pred = self.gnn_model.predict(node_features, edge_index)
                        gnn_pred = float(np.mean(gnn_pred))
                        predictions['gnn'] = gnn_pred
                        confidence_scores.append((self.gnn_weight, 0.7))
                        logger.debug(f"GNN prediction: {gnn_pred:.1f}%")
                except Exception as e:
                    logger.warning(f"GNN prediction failed: {e}")
                    predictions['gnn'] = 0
            
            # Calculate weighted ensemble prediction
            ensemble_pred = 0.0
            total_weight = 0.0
            
            if 'arima' in predictions and predictions['arima'] > 0:
                ensemble_pred += predictions['arima'] * self.arima_weight
                total_weight += self.arima_weight
            
            if 'lgbm' in predictions and predictions['lgbm'] > 0:
                ensemble_pred += predictions['lgbm'] * self.lgbm_weight
                total_weight += self.lgbm_weight
            
            if 'gnn' in predictions and predictions['gnn'] > 0:
                ensemble_pred += predictions['gnn'] * self.gnn_weight
                total_weight += self.gnn_weight
            
            if total_weight > 0:
                ensemble_pred = ensemble_pred / total_weight
            
            # Calculate ensemble confidence
            ensemble_confidence = np.mean([conf for _, conf in confidence_scores]) if confidence_scores else 0.7
            
            # Generate recommendation
            recommendation = self._get_recommendation(ensemble_pred)
            
            return {
                'discount_prediction': float(np.clip(ensemble_pred, 0, 100)),
                'models_used': list(predictions.keys()),
                'individual_predictions': predictions,
                'confidence': float(ensemble_confidence),
                'recommendation': recommendation,
                'weights': {
                    'arima': self.arima_weight,
                    'lgbm': self.lgbm_weight,
                    'gnn': self.gnn_weight
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            return {
                'discount_prediction': 0.0,
                'models_used': [],
                'confidence': 0.0,
                'recommendation': 'error',
                'error': str(e)
            }
    
    def _get_recommendation(self, discount_percent: float) -> str:
        """
        Get purchase recommendation based on prediction
        
        Args:
            discount_percent: Predicted discount percentage
        
        Returns:
            Recommendation (buy_now, wait, skip)
        """
        if discount_percent >= 30:
            return "buy_now"
        elif discount_percent >= 15:
            return "wait"
        else:
            return "skip"
    
    def update_weights(
        self,
        arima_weight: float = None,
        lgbm_weight: float = None,
        gnn_weight: float = None
    ) -> None:
        """
        Update model weights
        
        Args:
            arima_weight: New ARIMA weight
            lgbm_weight: New LightGBM weight
            gnn_weight: New GNN weight
        """
        weights = [
            arima_weight or self.arima_weight * sum([arima_weight or self.arima_weight, lgbm_weight or self.lgbm_weight, gnn_weight or self.gnn_weight]),
            lgbm_weight or self.lgbm_weight * sum([arima_weight or self.arima_weight, lgbm_weight or self.lgbm_weight, gnn_weight or self.gnn_weight]),
            gnn_weight or self.gnn_weight * sum([arima_weight or self.arima_weight, lgbm_weight or self.lgbm_weight, gnn_weight or self.gnn_weight])
        ]
        
        total = sum(weights)
        self.arima_weight = weights[0] / total
        self.lgbm_weight = weights[1] / total
        self.gnn_weight = weights[2] / total
        
        logger.info(f"Updated ensemble weights - ARIMA: {self.arima_weight:.2f}, LightGBM: {self.lgbm_weight:.2f}, GNN: {self.gnn_weight:.2f}")

# ============ Global Ensemble Instance ============

ensemble_predictor = EnsemblePredictor()
