"""
Minimal text analysis service that works without external dependencies.

This is a simplified version for testing and environments where
complex NLP libraries are not available.
"""
import re
import logging
from typing import Dict, Any, List
from collections import Counter


class MinimalSentimentAnalyzer:
    """Simple sentiment analysis using word lists."""

    def __init__(self):
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'perfect',
            'awesome', 'brilliant', 'outstanding', 'superb', 'magnificent'
        }

        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry',
            'sad', 'disappointed', 'frustrated', 'annoyed', 'disgusted', 'furious',
            'worst', 'pathetic', 'useless', 'stupid', 'ridiculous', 'garbage'
        }

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using simple word counting."""
        words = re.findall(r'\b\w+\b', text.lower())

        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            return {
                'score': 0.0,
                'confidence': 0.5,
                'label': 'neutral',
                'backend': 'minimal'
            }

        score = (positive_count - negative_count) / len(words) if words else 0
        confidence = total_sentiment_words / len(words) if words else 0

        if score > 0.1:
            label = 'positive'
        elif score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'score': score,
            'confidence': min(1.0, confidence * 5),  # Scale confidence
            'label': label,
            'backend': 'minimal'
        }


class MinimalTopicExtractor:
    """Simple topic extraction using keyword matching."""

    def __init__(self):
        self.topic_keywords = {
            'technology': ['tech', 'computer', 'software', 'digital', 'ai', 'programming', 'code'],
            'business': ['business', 'company', 'market', 'finance', 'money', 'profit', 'sales'],
            'sports': ['sport', 'game', 'team', 'player', 'match', 'competition', 'win'],
            'entertainment': ['movie', 'music', 'show', 'entertainment', 'film', 'actor', 'celebrity'],
            'health': ['health', 'medical', 'doctor', 'hospital', 'medicine', 'treatment'],
            'education': ['school', 'university', 'student', 'education', 'learning', 'teacher'],
            'politics': ['government', 'political', 'election', 'vote', 'policy', 'politician'],
            'science': ['science', 'research', 'study', 'experiment', 'discovery', 'theory']
        }

    def extract_topics(self, text: str) -> Dict[str, Any]:
        """Extract topics using keyword matching."""
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)

        # Score topics based on keyword matches
        topic_scores = {}
        for topic, keywords in self.topic_keywords.items():
            score = sum(word_freq.get(keyword, 0) for keyword in keywords)
            if score > 0:
                topic_scores[topic] = score

        # Determine primary topic
        if topic_scores:
            primary_topic = max(topic_scores.keys(), key=lambda k: topic_scores[k])
            confidence = topic_scores[primary_topic] / len(words) if words else 0
        else:
            primary_topic = 'general'
            confidence = 0.0

        # Extract keywords (most frequent words)
        keywords = [word for word, freq in word_freq.most_common(10) if len(word) > 2]

        return {
            'primary_topic': primary_topic,
            'topic_confidence': min(1.0, confidence * 10),
            'all_topics': list(topic_scores.items()),
            'keywords': keywords,
            'categories': list(topic_scores.keys())[:3],
            'content_type': 'general',
            'language': 'en'
        }


class MinimalTextAnalyzer:
    """Simple text quality analysis."""

    def __init__(self):
        self.spam_patterns = [
            r'\b(buy now|click here|free|win|winner)\b',
            r'\$\d+',
            r'[A-Z]{3,}',  # Excessive caps
            r'!{2,}',  # Multiple exclamation marks
        ]

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text quality using simple metrics."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        word_count = len(words)
        sentence_count = len(sentences)

        # Basic readability (average sentence length)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        if avg_sentence_length <= 10:
            readability_level = 'elementary'
        elif avg_sentence_length <= 15:
            readability_level = 'middle'
        elif avg_sentence_length <= 20:
            readability_level = 'high'
        else:
            readability_level = 'college'

        # Spam detection
        spam_score = 0
        text_lower = text.lower()
        for pattern in self.spam_patterns:
            matches = len(re.findall(pattern, text_lower))
            spam_score += matches * 0.2

        spam_probability = min(1.0, spam_score)

        # Quality score (inverse of spam + readability factor)
        quality_score = max(0.0, 1.0 - spam_probability)
        if word_count < 5:
            quality_score *= 0.5  # Penalize very short text

        # Complexity (lexical diversity)
        unique_words = len(set(word.lower() for word in words))
        complexity_score = unique_words / word_count if word_count > 0 else 0

        return {
            'quality_score': quality_score,
            'readability_level': readability_level,
            'complexity_score': complexity_score,
            'spam_probability': spam_probability,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'analysis_confidence': 0.8  # Fixed confidence for minimal analyzer
        }


class MinimalAnalyzer:
    """Combined minimal analyzer for all text analysis tasks."""

    def __init__(self):
        """Initialize all minimal analyzers."""
        self.sentiment_analyzer = MinimalSentimentAnalyzer()
        self.topic_extractor = MinimalTopicExtractor()
        self.text_analyzer = MinimalTextAnalyzer()
        self.logger = logging.getLogger(__name__)

    def analyze_all(self, text: str) -> Dict[str, Any]:
        """Perform all analysis tasks on the text."""
        try:
            sentiment = self.sentiment_analyzer.analyze_sentiment(text)
            topics = self.topic_extractor.extract_topics(text)
            quality = self.text_analyzer.analyze_text(text)

            return {
                'sentiment': sentiment,
                'topics': topics,
                'quality': quality,
                'backend': 'minimal'
            }
        except Exception as e:
            self.logger.error(f"Minimal analysis failed: {e}")
            return {
                'error': str(e),
                'backend': 'minimal'
            }


def test_minimal_analyzers():
    """Test the minimal analyzers."""
    print("🚀 Testing Minimal Analyzers")

    # Test sentiment
    print("\n1. Testing Sentiment Analysis:")
    sentiment_analyzer = MinimalSentimentAnalyzer()

    texts = [
        "I love this product! It's amazing and works perfectly.",
        "This is terrible. I hate it and it doesn't work.",
        "The weather is cloudy today."
    ]

    for text in texts:
        result = sentiment_analyzer.analyze_sentiment(text)
        print(f"   '{text[:30]}...' -> {result['label']} ({result['score']:.2f})")

    # Test topic extraction
    print("\n2. Testing Topic Extraction:")
    topic_extractor = MinimalTopicExtractor()

    texts = [
        "I'm learning Python programming and software development.",
        "The basketball team won the championship game last night.",
        "The new medical research shows promising results for treatment."
    ]

    for text in texts:
        result = topic_extractor.extract_topics(text)
        print(f"   '{text[:30]}...' -> {result['primary_topic']} (keywords: {result['keywords'][:3]})")

    # Test text analysis
    print("\n3. Testing Text Analysis:")
    text_analyzer = MinimalTextAnalyzer()

    texts = [
        "This is a well-written article about scientific research and methodology.",
        "BUY NOW!!! AMAZING DEAL!!! CLICK HERE!!!",
        "Short text."
    ]

    for text in texts:
        result = text_analyzer.analyze_text(text)
        print(f"   '{text[:30]}...' -> Quality: {result['quality_score']:.2f}, Spam: {result['spam_probability']:.2f}")

    print("\n✅ All minimal analyzers working correctly!")


if __name__ == "__main__":
    test_minimal_analyzers()
