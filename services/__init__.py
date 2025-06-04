"""
Services package for FIST Content Moderation System.

This package contains enhanced text analysis and processing services.
"""

# Import enhanced analysis services
try:
    from .sentiment_analyzer import get_sentiment_analyzer, SentimentAnalyzer, SentimentResult
    from .topic_extractor import get_topic_extractor, TopicExtractor, TopicResult
    from .text_analyzer import get_text_analyzer, TextAnalyzer, TextAnalysisResult
    from .content_processor import get_content_processor, IntelligentContentProcessor, process_content_intelligently
    from .threshold_manager import get_threshold_manager, DynamicThresholdManager, make_adaptive_decision

    __all__ = [
        'get_sentiment_analyzer', 'SentimentAnalyzer', 'SentimentResult',
        'get_topic_extractor', 'TopicExtractor', 'TopicResult',
        'get_text_analyzer', 'TextAnalyzer', 'TextAnalysisResult',
        'get_content_processor', 'IntelligentContentProcessor', 'process_content_intelligently',
        'get_threshold_manager', 'DynamicThresholdManager', 'make_adaptive_decision'
    ]
except ImportError as e:
    print(f"Warning: Some enhanced services not available: {e}")
    __all__ = []
