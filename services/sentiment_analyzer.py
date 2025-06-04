"""
Sentiment Analysis Service for FIST Content Moderation System.

This module provides multiple sentiment analysis backends for enhanced
content understanding and moderation context.
"""
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

# Import sentiment analysis libraries with fallbacks
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logging.warning("VADER sentiment analyzer not available")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("TextBlob not available")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available")


class SentimentBackend(Enum):
    """Available sentiment analysis backends."""
    VADER = "vader"
    TEXTBLOB = "textblob"
    TRANSFORMERS = "transformers"
    AUTO = "auto"


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    score: float  # -1.0 (negative) to 1.0 (positive)
    confidence: float  # 0.0 to 1.0
    label: str  # "positive", "negative", "neutral"
    backend: str  # Which backend was used
    raw_scores: Dict[str, float]  # Raw scores from the backend


class SentimentAnalyzer:
    """Multi-backend sentiment analysis service."""

    def __init__(self, preferred_backend: SentimentBackend = SentimentBackend.AUTO):
        """
        Initialize sentiment analyzer.

        Args:
            preferred_backend: Preferred sentiment analysis backend
        """
        self.preferred_backend = preferred_backend
        self.logger = logging.getLogger(__name__)

        # Initialize backends
        self._init_vader()
        self._init_transformers()

        # Determine best available backend
        self.available_backends = []
        if VADER_AVAILABLE and self.vader_analyzer is not None:
            self.available_backends.append(SentimentBackend.VADER)
        if TEXTBLOB_AVAILABLE:
            self.available_backends.append(SentimentBackend.TEXTBLOB)
        if TRANSFORMERS_AVAILABLE and self.transformers_analyzer is not None:
            self.available_backends.append(SentimentBackend.TRANSFORMERS)

        if not self.available_backends:
            raise RuntimeError("No sentiment analysis backends available")

        self.logger.info(f"Sentiment analyzer initialized with backends: {self.available_backends}")

    def _init_vader(self):
        """Initialize VADER sentiment analyzer."""
        self.vader_analyzer = None
        if VADER_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.logger.info("VADER sentiment analyzer initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize VADER: {e}")
                self.vader_analyzer = None

    def _init_transformers(self):
        """Initialize transformers sentiment analyzer."""
        self.transformers_analyzer = None
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model for sentiment analysis
                self.transformers_analyzer = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    return_all_scores=True
                )
                self.logger.info("Transformers sentiment analyzer initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize transformers sentiment analyzer: {e}")
                # Fallback to a simpler model
                try:
                    self.transformers_analyzer = pipeline(
                        "sentiment-analysis",
                        model="distilbert-base-uncased-finetuned-sst-2-english",
                        return_all_scores=True
                    )
                    self.logger.info("Transformers sentiment analyzer initialized with fallback model")
                except Exception as e2:
                    self.logger.error(f"Failed to initialize transformers with fallback: {e2}")
                    self.transformers_analyzer = None

    def analyze_sentiment(
        self,
        text: str,
        backend: Optional[SentimentBackend] = None
    ) -> SentimentResult:
        """
        Analyze sentiment of text using specified or best available backend.

        Args:
            text: Text to analyze
            backend: Specific backend to use (optional)

        Returns:
            SentimentResult with sentiment analysis
        """
        if not text or not text.strip():
            return SentimentResult(
                score=0.0,
                confidence=0.0,
                label="neutral",
                backend="none",
                raw_scores={}
            )

        # Determine which backend to use
        if backend is None:
            backend = self._get_best_backend()

        # Ensure backend is available
        if backend not in self.available_backends:
            backend = self._get_best_backend()

        try:
            if backend == SentimentBackend.VADER:
                return self._analyze_with_vader(text)
            elif backend == SentimentBackend.TEXTBLOB:
                return self._analyze_with_textblob(text)
            elif backend == SentimentBackend.TRANSFORMERS:
                return self._analyze_with_transformers(text)
            else:
                # Fallback to first available backend
                return self.analyze_sentiment(text, self.available_backends[0])

        except Exception as e:
            self.logger.error(f"Sentiment analysis failed with {backend}: {e}")
            # Try fallback backend
            if len(self.available_backends) > 1:
                fallback_backend = next(
                    (b for b in self.available_backends if b != backend),
                    self.available_backends[0]
                )
                return self.analyze_sentiment(text, fallback_backend)
            else:
                # Return neutral sentiment if all backends fail
                return SentimentResult(
                    score=0.0,
                    confidence=0.0,
                    label="neutral",
                    backend="error",
                    raw_scores={"error": str(e)}
                )

    def _get_best_backend(self) -> SentimentBackend:
        """Get the best available backend based on preferences."""
        if self.preferred_backend != SentimentBackend.AUTO and self.preferred_backend in self.available_backends:
            return self.preferred_backend

        # Priority order: TRANSFORMERS > VADER > TEXTBLOB
        if SentimentBackend.TRANSFORMERS in self.available_backends:
            return SentimentBackend.TRANSFORMERS
        elif SentimentBackend.VADER in self.available_backends:
            return SentimentBackend.VADER
        elif SentimentBackend.TEXTBLOB in self.available_backends:
            return SentimentBackend.TEXTBLOB
        else:
            return self.available_backends[0]

    def _analyze_with_vader(self, text: str) -> SentimentResult:
        """Analyze sentiment using VADER."""
        if self.vader_analyzer is None:
            raise RuntimeError("VADER analyzer not available")
        scores = self.vader_analyzer.polarity_scores(text)

        # VADER returns compound score (-1 to 1)
        compound_score = scores['compound']

        # Determine label and confidence
        if compound_score >= 0.05:
            label = "positive"
            confidence = abs(compound_score)
        elif compound_score <= -0.05:
            label = "negative"
            confidence = abs(compound_score)
        else:
            label = "neutral"
            confidence = 1.0 - abs(compound_score)

        return SentimentResult(
            score=compound_score,
            confidence=confidence,
            label=label,
            backend="vader",
            raw_scores=scores
        )

    def _analyze_with_textblob(self, text: str) -> SentimentResult:
        """Analyze sentiment using TextBlob."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1

        # Determine label
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"

        # Use subjectivity as confidence (more subjective = more confident)
        confidence = subjectivity

        return SentimentResult(
            score=polarity,
            confidence=confidence,
            label=label,
            backend="textblob",
            raw_scores={
                "polarity": polarity,
                "subjectivity": subjectivity
            }
        )

    def _analyze_with_transformers(self, text: str) -> SentimentResult:
        """Analyze sentiment using transformers."""
        if self.transformers_analyzer is None:
            raise RuntimeError("Transformers analyzer not available")

        # Truncate text if too long (transformers have token limits)
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]

        results = self.transformers_analyzer(text)[0]

        # Convert results to standardized format
        sentiment_map = {}
        for result in results:
            label = result['label'].lower()
            score = result['score']

            # Normalize labels
            if label in ['positive', 'pos', 'label_2']:
                sentiment_map['positive'] = score
            elif label in ['negative', 'neg', 'label_0']:
                sentiment_map['negative'] = score
            elif label in ['neutral', 'label_1']:
                sentiment_map['neutral'] = score

        # Determine dominant sentiment
        max_label = max(sentiment_map.keys(), key=lambda k: sentiment_map[k])
        max_score = sentiment_map[max_label]

        # Convert to -1 to 1 scale
        if max_label == 'positive':
            normalized_score = max_score
        elif max_label == 'negative':
            normalized_score = -max_score
        else:
            normalized_score = 0.0

        return SentimentResult(
            score=normalized_score,
            confidence=max_score,
            label=max_label,
            backend="transformers",
            raw_scores=sentiment_map
        )

    def get_sentiment_context(self, sentiment_result: SentimentResult) -> Dict[str, Any]:
        """
        Get additional context for content moderation based on sentiment.

        Args:
            sentiment_result: Sentiment analysis result

        Returns:
            Dictionary with sentiment context for moderation
        """
        context = {
            "sentiment_score": sentiment_result.score,
            "sentiment_label": sentiment_result.label,
            "sentiment_confidence": sentiment_result.confidence,
            "sentiment_backend": sentiment_result.backend
        }

        # Add risk indicators based on sentiment
        if sentiment_result.label == "negative" and sentiment_result.confidence > 0.7:
            context["high_negative_sentiment"] = True
            context["moderation_note"] = "Content shows strong negative sentiment"
        elif sentiment_result.label == "positive" and sentiment_result.confidence > 0.8:
            context["high_positive_sentiment"] = True
            context["moderation_note"] = "Content shows strong positive sentiment"
        else:
            context["neutral_sentiment"] = True
            context["moderation_note"] = "Content has neutral or mixed sentiment"

        # Add sentiment-based moderation suggestions
        if sentiment_result.score < -0.5:
            context["suggested_action"] = "review_for_negativity"
        elif sentiment_result.score > 0.5:
            context["suggested_action"] = "likely_positive"
        else:
            context["suggested_action"] = "standard_review"

        return context


# Global sentiment analyzer instance
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


def analyze_text_sentiment(text: str) -> SentimentResult:
    """
    Convenience function to analyze text sentiment.

    Args:
        text: Text to analyze

    Returns:
        SentimentResult
    """
    analyzer = get_sentiment_analyzer()
    return analyzer.analyze_sentiment(text)
