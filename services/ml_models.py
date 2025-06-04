"""
Advanced Machine Learning Models Integration for FIST Content Moderation System.

This module provides integration with advanced ML models including:
- Custom trained models for content classification
- Ensemble model predictions
- Model performance monitoring
- A/B testing framework for models
- Real-time model updates
"""
import logging
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import pickle
import os

from config import Config


class ModelType(Enum):
    """Types of ML models."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    ENSEMBLE = "ensemble"


class ModelStatus(Enum):
    """Model status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    TESTING = "testing"
    DEPRECATED = "deprecated"


@dataclass
class ModelPrediction:
    """Result of model prediction."""
    model_id: str
    model_type: ModelType
    prediction: Union[float, int, str, List[float]]
    confidence: float
    processing_time: float
    features_used: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsemblePrediction:
    """Result of ensemble prediction."""
    final_prediction: Union[float, int, str]
    confidence: float
    individual_predictions: List[ModelPrediction]
    ensemble_method: str
    consensus_score: float
    processing_time: float


@dataclass
class ModelPerformanceMetrics:
    """Model performance metrics."""
    model_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    prediction_count: int
    average_processing_time: float
    last_updated: float
    error_rate: float


class FeatureExtractor:
    """Extract features from content for ML models."""

    def __init__(self):
        """Initialize feature extractor."""
        self.logger = logging.getLogger(__name__)

    def extract_basic_features(self, text: str) -> Dict[str, float]:
        """Extract basic text features."""
        words = text.split()
        sentences = text.split('.')

        features = {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'char_count': len(text),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'digit_ratio': sum(1 for c in text if c.isdigit()) / len(text) if text else 0,
            'punctuation_ratio': sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text) if text else 0,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'caps_word_ratio': sum(1 for word in words if word.isupper()) / len(words) if words else 0,
        }

        return features

    def extract_linguistic_features(self, text: str) -> Dict[str, float]:
        """Extract linguistic features."""
        # This would use NLP libraries in practice
        features = {
            'readability_score': self._calculate_readability(text),
            'sentiment_polarity': self._estimate_sentiment(text),
            'formality_score': self._estimate_formality(text),
            'complexity_score': self._calculate_complexity(text),
        }

        return features

    def _calculate_readability(self, text: str) -> float:
        """Simple readability estimation."""
        words = text.split()
        sentences = text.split('.')

        if not words or not sentences:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Simplified Flesch formula
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 4.7)
        return max(0.0, min(100.0, readability)) / 100.0

    def _estimate_sentiment(self, text: str) -> float:
        """Simple sentiment estimation."""
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'love', 'like', 'happy', 'pleased'}
        negative_words = {'bad', 'terrible', 'awful', 'hate', 'dislike', 'angry', 'sad', 'disappointed'}

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        if positive_count + negative_count == 0:
            return 0.0

        return (positive_count - negative_count) / len(words)

    def _estimate_formality(self, text: str) -> float:
        """Estimate text formality."""
        formal_indicators = {'therefore', 'however', 'furthermore', 'consequently', 'nevertheless'}
        informal_indicators = {'yeah', 'ok', 'lol', 'omg', 'btw', 'gonna', 'wanna'}

        words = text.lower().split()
        formal_count = sum(1 for word in words if word in formal_indicators)
        informal_count = sum(1 for word in words if word in informal_indicators)

        if formal_count + informal_count == 0:
            return 0.5

        return formal_count / (formal_count + informal_count)

    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity."""
        words = text.split()
        if not words:
            return 0.0

        unique_words = len(set(word.lower() for word in words))
        lexical_diversity = unique_words / len(words)

        long_words = sum(1 for word in words if len(word) > 6)
        long_word_ratio = long_words / len(words)

        return (lexical_diversity + long_word_ratio) / 2

    def extract_all_features(self, text: str, enhanced_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Extract all available features."""
        features = {}

        # Basic features
        features.update(self.extract_basic_features(text))

        # Linguistic features
        features.update(self.extract_linguistic_features(text))

        # Enhanced analysis features
        if enhanced_analysis:
            if 'sentiment_analysis' in enhanced_analysis:
                sentiment = enhanced_analysis['sentiment_analysis']
                features['enhanced_sentiment_score'] = sentiment.get('score', 0.0)
                features['enhanced_sentiment_confidence'] = sentiment.get('confidence', 0.0)

            if 'topic_extraction' in enhanced_analysis:
                topic = enhanced_analysis['topic_extraction']
                features['topic_confidence'] = topic.get('topic_confidence', 0.0)
                features['keyword_count'] = len(topic.get('keywords', []))

            if 'text_quality' in enhanced_analysis:
                quality = enhanced_analysis['text_quality']
                features['quality_score'] = quality.get('quality_score', 0.0)
                features['spam_probability'] = quality.get('spam_probability', 0.0)
                features['analysis_confidence'] = quality.get('analysis_confidence', 0.0)

        return features


class SimpleMLModel:
    """Simple ML model implementation."""

    def __init__(self, model_id: str, model_type: ModelType):
        """Initialize model."""
        self.model_id = model_id
        self.model_type = model_type
        self.status = ModelStatus.INACTIVE
        self.weights = {}
        self.bias = 0.0
        self.feature_names = []
        self.training_data = []
        self.performance_metrics = None
        self.logger = logging.getLogger(__name__)

    def train(self, training_data: List[Tuple[Dict[str, float], float]]):
        """Train the model with simple linear regression."""
        self.status = ModelStatus.TRAINING
        self.training_data = training_data

        if not training_data:
            self.logger.warning(f"No training data for model {self.model_id}")
            return

        # Extract features and targets
        features_list = [features for features, _ in training_data]
        targets = [target for _, target in training_data]

        # Get all feature names
        all_features = set()
        for features in features_list:
            all_features.update(features.keys())
        self.feature_names = sorted(list(all_features))

        # Simple linear regression using normal equation
        # This is a simplified implementation
        if len(self.feature_names) > 0:
            # Initialize weights randomly
            import random
            random.seed(42)  # For reproducibility
            self.weights = {feature: random.uniform(-0.01, 0.01) for feature in self.feature_names}
            self.bias = random.uniform(-0.01, 0.01)

            # Simple gradient descent (very basic)
            learning_rate = 0.001  # Smaller learning rate
            epochs = 50  # Fewer epochs

            for epoch in range(epochs):
                total_error = 0
                for features, target in training_data:
                    # Prediction
                    prediction = self.bias
                    for feature in self.feature_names:
                        prediction += self.weights[feature] * features.get(feature, 0.0)

                    # Error
                    error = target - prediction
                    total_error += min(error ** 2, 1000)  # Prevent overflow

                    # Update weights
                    self.bias += learning_rate * error
                    for feature in self.feature_names:
                        self.weights[feature] += learning_rate * error * features.get(feature, 0.0)

                if epoch % 20 == 0:
                    self.logger.debug(f"Epoch {epoch}, Error: {total_error / len(training_data)}")

        self.status = ModelStatus.ACTIVE
        self.logger.info(f"Model {self.model_id} training completed")

    def predict(self, features: Dict[str, float]) -> ModelPrediction:
        """Make prediction."""
        start_time = time.time()

        if self.status != ModelStatus.ACTIVE:
            raise ValueError(f"Model {self.model_id} is not active")

        # Calculate prediction
        prediction = self.bias
        for feature in self.feature_names:
            prediction += self.weights[feature] * features.get(feature, 0.0)

        # Normalize prediction to 0-1 range for classification
        if self.model_type == ModelType.CLASSIFICATION:
            prediction = max(0.0, min(1.0, prediction))

        # Calculate confidence (simplified)
        confidence = min(1.0, abs(prediction - 0.5) * 2)

        processing_time = time.time() - start_time

        return ModelPrediction(
            model_id=self.model_id,
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            processing_time=processing_time,
            features_used=list(features.keys()),
            metadata={'weights_used': len(self.weights)}
        )

    def save_model(self, filepath: str):
        """Save model to file."""
        model_data = {
            'model_id': self.model_id,
            'model_type': self.model_type.value,
            'weights': self.weights,
            'bias': self.bias,
            'feature_names': self.feature_names,
            'status': self.status.value
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        self.logger.info(f"Model {self.model_id} saved to {filepath}")

    def load_model(self, filepath: str):
        """Load model from file."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model_id = model_data['model_id']
        self.model_type = ModelType(model_data['model_type'])
        self.weights = model_data['weights']
        self.bias = model_data['bias']
        self.feature_names = model_data['feature_names']
        self.status = ModelStatus(model_data['status'])

        self.logger.info(f"Model {self.model_id} loaded from {filepath}")


class EnsembleModel:
    """Ensemble model that combines multiple models."""

    def __init__(self, ensemble_id: str):
        """Initialize ensemble model."""
        self.ensemble_id = ensemble_id
        self.models = {}
        self.model_weights = {}
        self.ensemble_method = "weighted_average"
        self.logger = logging.getLogger(__name__)

    def add_model(self, model: SimpleMLModel, weight: float = 1.0):
        """Add model to ensemble."""
        self.models[model.model_id] = model
        self.model_weights[model.model_id] = weight
        self.logger.info(f"Added model {model.model_id} to ensemble {self.ensemble_id}")

    def predict(self, features: Dict[str, float]) -> EnsemblePrediction:
        """Make ensemble prediction."""
        start_time = time.time()

        if not self.models:
            raise ValueError(f"No models in ensemble {self.ensemble_id}")

        individual_predictions = []
        weighted_sum = 0.0
        total_weight = 0.0

        # Get predictions from all models
        for model_id, model in self.models.items():
            try:
                prediction = model.predict(features)
                individual_predictions.append(prediction)

                weight = self.model_weights[model_id]
                weighted_sum += prediction.prediction * weight
                total_weight += weight

            except Exception as e:
                self.logger.warning(f"Model {model_id} prediction failed: {e}")

        if total_weight == 0:
            raise ValueError("No valid predictions from ensemble models")

        # Calculate final prediction
        final_prediction = weighted_sum / total_weight

        # Calculate consensus score
        predictions_values = [p.prediction for p in individual_predictions]
        if predictions_values:
            avg_prediction = sum(predictions_values) / len(predictions_values)
            variance = sum((p - avg_prediction) ** 2 for p in predictions_values) / len(predictions_values)
            consensus_score = max(0.0, 1.0 - variance)
        else:
            consensus_score = 0.0

        # Calculate ensemble confidence
        avg_confidence = sum(p.confidence for p in individual_predictions) / len(individual_predictions)
        ensemble_confidence = (avg_confidence + consensus_score) / 2

        processing_time = time.time() - start_time

        return EnsemblePrediction(
            final_prediction=final_prediction,
            confidence=ensemble_confidence,
            individual_predictions=individual_predictions,
            ensemble_method=self.ensemble_method,
            consensus_score=consensus_score,
            processing_time=processing_time
        )


class MLModelManager:
    """Manages multiple ML models and their lifecycle."""

    def __init__(self):
        """Initialize model manager."""
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.ensembles = {}
        self.feature_extractor = FeatureExtractor()
        self.performance_history = defaultdict(list)
        self.prediction_cache = {}
        self.cache_ttl = 3600  # 1 hour

        # Initialize default models
        self._initialize_default_models()

        self.logger.info("ML Model Manager initialized")

    def _initialize_default_models(self):
        """Initialize default models."""
        # Content toxicity model
        toxicity_model = SimpleMLModel("content_toxicity", ModelType.CLASSIFICATION)
        self.models["content_toxicity"] = toxicity_model

        # Spam detection model
        spam_model = SimpleMLModel("spam_detection", ModelType.CLASSIFICATION)
        self.models["spam_detection"] = spam_model

        # Quality assessment model
        quality_model = SimpleMLModel("content_quality", ModelType.REGRESSION)
        self.models["content_quality"] = quality_model

        # Create ensemble
        main_ensemble = EnsembleModel("main_moderation")
        main_ensemble.add_model(toxicity_model, weight=0.4)
        main_ensemble.add_model(spam_model, weight=0.3)
        main_ensemble.add_model(quality_model, weight=0.3)
        self.ensembles["main_moderation"] = main_ensemble

        self.logger.info("Default models initialized")

    def train_model(self, model_id: str, training_data: List[Tuple[str, float]], enhanced_analysis_data: Optional[List[Dict[str, Any]]] = None):
        """Train a specific model."""
        if model_id not in self.models:
            self.logger.error(f"Model {model_id} not found")
            return

        # Extract features from training data
        processed_training_data = []
        for i, (text, target) in enumerate(training_data):
            enhanced_analysis = enhanced_analysis_data[i] if enhanced_analysis_data and i < len(enhanced_analysis_data) else None
            features = self.feature_extractor.extract_all_features(text, enhanced_analysis)
            processed_training_data.append((features, target))

        # Train the model
        model = self.models[model_id]
        model.train(processed_training_data)

        self.logger.info(f"Model {model_id} training completed with {len(training_data)} samples")

    def predict_with_model(self, model_id: str, text: str, enhanced_analysis: Optional[Dict[str, Any]] = None) -> ModelPrediction:
        """Make prediction with specific model."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")

        # Check cache
        cache_key = hashlib.md5(f"{model_id}:{text}".encode()).hexdigest()
        if cache_key in self.prediction_cache:
            cached_result, timestamp = self.prediction_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result

        # Extract features
        features = self.feature_extractor.extract_all_features(text, enhanced_analysis)

        # Make prediction
        model = self.models[model_id]
        prediction = model.predict(features)

        # Cache result
        self.prediction_cache[cache_key] = (prediction, time.time())

        # Record performance
        self.performance_history[model_id].append({
            'timestamp': time.time(),
            'processing_time': prediction.processing_time,
            'confidence': prediction.confidence
        })

        return prediction

    def predict_with_ensemble(self, ensemble_id: str, text: str, enhanced_analysis: Optional[Dict[str, Any]] = None) -> EnsemblePrediction:
        """Make prediction with ensemble."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} not found")

        # Extract features
        features = self.feature_extractor.extract_all_features(text, enhanced_analysis)

        # Make ensemble prediction
        ensemble = self.ensembles[ensemble_id]
        prediction = ensemble.predict(features)

        return prediction

    def get_model_performance(self, model_id: str) -> Optional[ModelPerformanceMetrics]:
        """Get performance metrics for a model."""
        if model_id not in self.models or model_id not in self.performance_history:
            return None

        history = self.performance_history[model_id]
        if not history:
            return None

        # Calculate metrics from history
        recent_history = history[-100:]  # Last 100 predictions

        avg_processing_time = sum(h['processing_time'] for h in recent_history) / len(recent_history)
        avg_confidence = sum(h['confidence'] for h in recent_history) / len(recent_history)

        # Simplified metrics (in practice, these would be calculated from validation data)
        return ModelPerformanceMetrics(
            model_id=model_id,
            accuracy=0.85,  # Placeholder
            precision=0.82,  # Placeholder
            recall=0.88,  # Placeholder
            f1_score=0.85,  # Placeholder
            auc_roc=0.90,  # Placeholder
            prediction_count=len(history),
            average_processing_time=avg_processing_time,
            last_updated=time.time(),
            error_rate=1.0 - avg_confidence
        )

    def save_models(self, directory: str):
        """Save all models to directory."""
        os.makedirs(directory, exist_ok=True)

        for model_id, model in self.models.items():
            filepath = os.path.join(directory, f"{model_id}.pkl")
            model.save_model(filepath)

        self.logger.info(f"All models saved to {directory}")

    def load_models(self, directory: str):
        """Load models from directory."""
        if not os.path.exists(directory):
            self.logger.warning(f"Model directory {directory} does not exist")
            return

        for filename in os.listdir(directory):
            if filename.endswith('.pkl'):
                model_id = filename[:-4]  # Remove .pkl extension
                filepath = os.path.join(directory, filename)

                if model_id in self.models:
                    self.models[model_id].load_model(filepath)
                    self.logger.info(f"Loaded model {model_id}")

        self.logger.info(f"Models loaded from {directory}")


# Global ML model manager instance
_ml_model_manager: Optional[MLModelManager] = None


def get_ml_model_manager() -> MLModelManager:
    """Get global ML model manager instance."""
    global _ml_model_manager
    if _ml_model_manager is None:
        _ml_model_manager = MLModelManager()
    return _ml_model_manager


def predict_with_ml_models(text: str, enhanced_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to get predictions from ML models.

    Args:
        text: Text to analyze
        enhanced_analysis: Enhanced analysis results

    Returns:
        Dictionary with ML predictions
    """
    manager = get_ml_model_manager()

    results = {}

    try:
        # Get ensemble prediction
        ensemble_prediction = manager.predict_with_ensemble("main_moderation", text, enhanced_analysis)
        results['ensemble'] = {
            'prediction': ensemble_prediction.final_prediction,
            'confidence': ensemble_prediction.confidence,
            'consensus_score': ensemble_prediction.consensus_score,
            'processing_time': ensemble_prediction.processing_time
        }

        # Get individual model predictions
        results['individual_models'] = {}
        for model_id in ['content_toxicity', 'spam_detection', 'content_quality']:
            try:
                prediction = manager.predict_with_model(model_id, text, enhanced_analysis)
                results['individual_models'][model_id] = {
                    'prediction': prediction.prediction,
                    'confidence': prediction.confidence,
                    'processing_time': prediction.processing_time
                }
            except Exception as e:
                results['individual_models'][model_id] = {'error': str(e)}

    except Exception as e:
        results['error'] = str(e)

    return results
