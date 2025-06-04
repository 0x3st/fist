"""
AI and Enhanced Analysis Services for FIST Content Moderation System.

This package contains all AI-powered analysis components:
- AI connector for external services
- Sentiment analysis
- Topic extraction
- Text quality analysis
- Content processing
- Threshold management
- Machine learning models
- Feedback and learning systems
- Multi-language processing
- Cultural analysis
- Semantic caching
"""

# Core AI connector
from .ai_connector import AIConnector

# Enhanced analysis services
try:
    from .sentiment_analyzer import get_sentiment_analyzer, SentimentAnalyzer, SentimentResult
    from .topic_extractor import get_topic_extractor, TopicExtractor, TopicResult
    from .text_analyzer import get_text_analyzer, TextAnalyzer, TextAnalysisResult
    from .content_processor import get_content_processor, IntelligentContentProcessor, process_content_intelligently
    from .threshold_manager import get_threshold_manager, DynamicThresholdManager, make_adaptive_decision
    from .ml_models import get_ml_model_manager, MLModelManager
    from .feedback_system import get_learning_engine, get_feedback_collector
    from .language_detector import detect_and_process_text
    from .multilingual_processor import get_multilingual_processor
    from .cultural_analyzer import analyze_cultural_context, CulturalContextAnalyzer
    from .semantic_cache import get_semantic_cache_manager, get_cached_moderation_result, store_moderation_result
    from .minimal_analyzer import MinimalAnalyzer

    __all__ = [
        'AIConnector',
        'get_sentiment_analyzer', 'SentimentAnalyzer', 'SentimentResult',
        'get_topic_extractor', 'TopicExtractor', 'TopicResult',
        'get_text_analyzer', 'TextAnalyzer', 'TextAnalysisResult',
        'get_content_processor', 'IntelligentContentProcessor', 'process_content_intelligently',
        'get_threshold_manager', 'DynamicThresholdManager', 'make_adaptive_decision',
        'get_ml_model_manager', 'MLModelManager',
        'get_learning_engine', 'get_feedback_collector',
        'detect_and_process_text', 'get_multilingual_processor',
        'analyze_cultural_context', 'CulturalContextAnalyzer',
        'get_semantic_cache_manager', 'get_cached_moderation_result', 'store_moderation_result',
        'MinimalAnalyzer'
    ]
except ImportError as e:
    print(f"Warning: Some AI services not available: {e}")
    __all__ = ['AIConnector']
