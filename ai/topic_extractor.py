"""
Topic Extraction Service for FIST Content Moderation System.

This module provides topic modeling and content categorization capabilities
for enhanced content understanding and context-aware moderation.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union, Set
from dataclasses import dataclass
from collections import Counter

# Import NLP libraries with fallbacks
try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available")


@dataclass
class TopicResult:
    """Topic extraction result."""
    primary_topic: str
    topic_confidence: float
    all_topics: List[Tuple[str, float]]  # (topic, confidence) pairs
    keywords: List[str]
    categories: List[str]
    content_type: str
    language: str


@dataclass
class KeywordResult:
    """Keyword extraction result."""
    keywords: List[str]
    keyword_scores: Dict[str, float]
    entities: List[Dict[str, Any]]
    phrases: List[str]


class TopicExtractor:
    """Advanced topic extraction and content categorization service."""

    def __init__(self):
        """Initialize topic extractor."""
        self.logger = logging.getLogger(__name__)

        # Initialize NLP components
        self._init_spacy()
        self._init_nltk()
        self._init_sklearn()

        # Predefined topic categories
        self.topic_categories = {
            "technology": ["tech", "software", "computer", "digital", "ai", "machine learning", "programming"],
            "politics": ["government", "election", "policy", "political", "vote", "democracy", "politician"],
            "sports": ["game", "team", "player", "sport", "match", "competition", "tournament"],
            "entertainment": ["movie", "music", "celebrity", "show", "entertainment", "film", "actor"],
            "business": ["company", "market", "business", "finance", "economy", "investment", "corporate"],
            "health": ["health", "medical", "doctor", "hospital", "medicine", "treatment", "disease"],
            "education": ["school", "university", "student", "education", "learning", "academic", "teacher"],
            "news": ["news", "report", "breaking", "update", "announcement", "press", "media"],
            "social": ["social", "community", "people", "society", "culture", "relationship", "family"],
            "science": ["science", "research", "study", "experiment", "discovery", "scientific", "theory"]
        }

        # Content type patterns
        self.content_type_patterns = {
            "social_media": [r"#\w+", r"@\w+", r"\b(like|share|follow|retweet)\b"],
            "news": [r"\b(breaking|update|report|announced)\b", r"\d{4}-\d{2}-\d{2}", r"\b(according to|sources say)\b"],
            "review": [r"\b(rating|stars|review|recommend)\b", r"\b\d+/\d+\b", r"\b(pros|cons|verdict)\b"],
            "comment": [r"\b(think|opinion|believe|feel)\b", r"\b(agree|disagree)\b", r"\b(imho|imo)\b"],
            "question": [r"\?", r"\b(how|what|why|when|where|who)\b", r"\b(help|advice|suggestion)\b"],
            "promotional": [r"\b(buy|sale|discount|offer|deal)\b", r"\$\d+", r"\b(limited time|act now)\b"]
        }

        self.logger.info("Topic extractor initialized")

    def _init_spacy(self):
        """Initialize spaCy NLP pipeline."""
        if SPACY_AVAILABLE:
            try:
                # Try to load the full model first
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("spaCy model loaded successfully")
            except OSError:
                try:
                    # Fallback to basic English model
                    self.nlp = English()
                    self.logger.warning("Using basic English model as fallback")
                except Exception as e:
                    self.logger.error(f"Failed to initialize spaCy: {e}")
                    self.nlp = None
        else:
            self.nlp = None

    def _init_nltk(self):
        """Initialize NLTK components."""
        self.stop_words = set()
        self.lemmatizer = None

        if NLTK_AVAILABLE:
            try:
                # Try to use NLTK data if already available, don't download
                try:
                    # Test if data is already available
                    self.stop_words = set(stopwords.words('english'))
                    self.lemmatizer = WordNetLemmatizer()
                    self.logger.info("NLTK initialized with existing data")
                except LookupError:
                    # Data not available, try to download with timeout
                    self.logger.warning("NLTK data not found, attempting download...")
                    try:
                        # Set a timeout for downloads
                        import socket
                        socket.setdefaulttimeout(5)  # 5 second timeout

                        nltk.download('punkt', quiet=True)
                        nltk.download('stopwords', quiet=True)
                        nltk.download('wordnet', quiet=True)
                        nltk.download('averaged_perceptron_tagger', quiet=True)

                        self.stop_words = set(stopwords.words('english'))
                        self.lemmatizer = WordNetLemmatizer()
                        self.logger.info("NLTK initialized with downloaded data")
                    except Exception as download_error:
                        self.logger.warning(f"NLTK download failed: {download_error}")
                        # Use basic fallback
                        self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
                        self.lemmatizer = None
                        self.logger.info("Using basic stopwords fallback")
                    finally:
                        # Reset timeout
                        socket.setdefaulttimeout(None)

            except Exception as e:
                self.logger.error(f"Failed to initialize NLTK: {e}")
                # Use basic fallback
                self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
                self.lemmatizer = None

    def _init_sklearn(self):
        """Initialize scikit-learn components."""
        if SKLEARN_AVAILABLE:
            try:
                # Initialize TF-IDF vectorizer
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95
                )

                # Initialize LDA for topic modeling
                self.lda_model = LatentDirichletAllocation(
                    n_components=10,
                    random_state=42,
                    max_iter=10
                )

                self.logger.info("scikit-learn components initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize scikit-learn: {e}")
                self.tfidf_vectorizer = None
                self.lda_model = None
        else:
            self.tfidf_vectorizer = None
            self.lda_model = None

    def extract_topics(self, text: str) -> TopicResult:
        """
        Extract topics from text using multiple approaches.

        Args:
            text: Text to analyze

        Returns:
            TopicResult with topic information
        """
        if not text or not text.strip():
            return TopicResult(
                primary_topic="unknown",
                topic_confidence=0.0,
                all_topics=[],
                keywords=[],
                categories=[],
                content_type="unknown",
                language="unknown"
            )

        try:
            # Extract keywords first
            keyword_result = self.extract_keywords(text)

            # Detect content type
            content_type = self._detect_content_type(text)

            # Detect language (simple heuristic)
            language = self._detect_language(text)

            # Category-based topic detection
            categories = self._categorize_content(text, keyword_result.keywords)

            # Rule-based topic extraction
            rule_based_topics = self._extract_topics_rule_based(text, keyword_result.keywords)

            # Statistical topic extraction (if available)
            statistical_topics = []
            if SKLEARN_AVAILABLE and self.tfidf_vectorizer and len(text.split()) > 10:
                statistical_topics = self._extract_topics_statistical(text)

            # Combine and rank topics
            all_topics = self._combine_topics(rule_based_topics, statistical_topics, categories)

            # Determine primary topic
            primary_topic = all_topics[0][0] if all_topics else "general"
            topic_confidence = all_topics[0][1] if all_topics else 0.0

            return TopicResult(
                primary_topic=primary_topic,
                topic_confidence=topic_confidence,
                all_topics=all_topics[:5],  # Top 5 topics
                keywords=keyword_result.keywords[:10],  # Top 10 keywords
                categories=categories,
                content_type=content_type,
                language=language
            )

        except Exception as e:
            self.logger.error(f"Topic extraction failed: {e}")
            return TopicResult(
                primary_topic="error",
                topic_confidence=0.0,
                all_topics=[],
                keywords=[],
                categories=[],
                content_type="unknown",
                language="unknown"
            )

    def extract_keywords(self, text: str) -> KeywordResult:
        """
        Extract keywords and key phrases from text.

        Args:
            text: Text to analyze

        Returns:
            KeywordResult with extracted keywords
        """
        keywords = []
        keyword_scores = {}
        entities = []
        phrases = []

        try:
            # spaCy-based extraction
            if self.nlp:
                doc = self.nlp(text)

                # Extract named entities
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "description": spacy.explain(ent.label_) or ent.label_
                    })

                # Extract noun phrases
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) <= 3:  # Limit phrase length
                        phrases.append(chunk.text.lower())

                # Extract keywords (nouns, adjectives, proper nouns)
                for token in doc:
                    if (token.pos_ in ['NOUN', 'ADJ', 'PROPN'] and
                        not token.is_stop and
                        not token.is_punct and
                        len(token.text) > 2):
                        keywords.append(token.lemma_.lower())

            # NLTK-based extraction (fallback)
            elif NLTK_AVAILABLE:
                tokens = word_tokenize(text.lower())
                # Simple keyword extraction based on word frequency
                word_freq = Counter([
                    word for word in tokens
                    if word.isalpha() and
                    word not in self.stop_words and
                    len(word) > 2
                ])
                keywords = [word for word, _ in word_freq.most_common(20)]

            # Simple regex-based extraction (final fallback)
            else:
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                word_freq = Counter(words)
                keywords = [word for word, _ in word_freq.most_common(20)]

            # Calculate keyword scores (simple frequency-based)
            if keywords:
                total_words = len(text.split())
                for keyword in keywords:
                    count = text.lower().count(keyword)
                    keyword_scores[keyword] = count / total_words

            # Remove duplicates and sort
            keywords = list(dict.fromkeys(keywords))  # Preserve order while removing duplicates
            phrases = list(dict.fromkeys(phrases))

            return KeywordResult(
                keywords=keywords[:20],  # Top 20 keywords
                keyword_scores=keyword_scores,
                entities=entities,
                phrases=phrases[:10]  # Top 10 phrases
            )

        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return KeywordResult(
                keywords=[],
                keyword_scores={},
                entities=[],
                phrases=[]
            )

    def _detect_content_type(self, text: str) -> str:
        """Detect content type based on patterns."""
        text_lower = text.lower()

        type_scores = {}
        for content_type, patterns in self.content_type_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            type_scores[content_type] = score

        # Return type with highest score, or "general" if no clear type
        if type_scores and max(type_scores.values()) > 0:
            return max(type_scores.keys(), key=lambda k: type_scores[k])
        return "general"

    def _detect_language(self, text: str) -> str:
        """Simple language detection (placeholder for more sophisticated detection)."""
        # This is a very basic implementation
        # In a real system, you'd use langdetect or similar

        # Check for common non-English patterns
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        if chinese_chars > len(text) * 0.1:
            return "zh"

        # Default to English for now
        return "en"

    def _categorize_content(self, text: str, keywords: List[str]) -> List[str]:
        """Categorize content based on predefined categories."""
        text_lower = text.lower()
        categories = []

        for category, category_keywords in self.topic_categories.items():
            score = 0

            # Check text content
            for keyword in category_keywords:
                if keyword in text_lower:
                    score += text_lower.count(keyword)

            # Check extracted keywords
            for keyword in keywords:
                if keyword in category_keywords:
                    score += 2  # Higher weight for extracted keywords

            if score > 0:
                categories.append((category, score))

        # Sort by score and return category names
        categories.sort(key=lambda x: x[1], reverse=True)
        return [cat[0] for cat in categories[:3]]  # Top 3 categories

    def _extract_topics_rule_based(self, text: str, keywords: List[str]) -> List[Tuple[str, float]]:
        """Extract topics using rule-based approach."""
        topics = []

        # Use categories as topics
        categories = self._categorize_content(text, keywords)
        for i, category in enumerate(categories):
            confidence = 1.0 - (i * 0.2)  # Decreasing confidence
            topics.append((category, confidence))

        # Add keyword-based topics
        if keywords:
            # Group similar keywords as topics
            for keyword in keywords[:5]:  # Top 5 keywords as potential topics
                confidence = 0.5  # Medium confidence for keyword-based topics
                topics.append((keyword, confidence))

        return topics

    def _extract_topics_statistical(self, text: str) -> List[Tuple[str, float]]:
        """Extract topics using statistical methods (LDA)."""
        if not SKLEARN_AVAILABLE or not self.tfidf_vectorizer:
            return []

        try:
            # Prepare text for LDA
            texts = [text]  # Single document

            # Vectorize text
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)

            # Apply LDA
            lda_output = self.lda_model.fit_transform(tfidf_matrix)

            # Get feature names (words)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()

            # Extract topics
            topics = []
            for topic_idx, topic in enumerate(self.lda_model.components_):
                # Get top words for this topic
                top_words_idx = topic.argsort()[-5:][::-1]  # Top 5 words
                top_words = [feature_names[i] for i in top_words_idx]

                # Create topic name from top words
                topic_name = "_".join(top_words[:2])  # Use top 2 words

                # Get topic probability for this document
                topic_prob = lda_output[0][topic_idx]

                if topic_prob > 0.1:  # Only include topics with reasonable probability
                    topics.append((topic_name, topic_prob))

            return topics

        except Exception as e:
            self.logger.error(f"Statistical topic extraction failed: {e}")
            return []

    def _combine_topics(
        self,
        rule_based: List[Tuple[str, float]],
        statistical: List[Tuple[str, float]],
        categories: List[str]
    ) -> List[Tuple[str, float]]:
        """Combine topics from different methods."""
        combined = {}

        # Add rule-based topics
        for topic, confidence in rule_based:
            combined[topic] = combined.get(topic, 0) + confidence * 0.6

        # Add statistical topics
        for topic, confidence in statistical:
            combined[topic] = combined.get(topic, 0) + confidence * 0.4

        # Boost category-based topics
        for category in categories:
            if category in combined:
                combined[category] *= 1.5

        # Sort by combined confidence
        sorted_topics = sorted(combined.items(), key=lambda x: x[1], reverse=True)

        return sorted_topics

    def get_topic_context(self, topic_result: TopicResult) -> Dict[str, Any]:
        """
        Get additional context for content moderation based on topics.

        Args:
            topic_result: Topic extraction result

        Returns:
            Dictionary with topic context for moderation
        """
        context = {
            "primary_topic": topic_result.primary_topic,
            "topic_confidence": topic_result.topic_confidence,
            "content_type": topic_result.content_type,
            "language": topic_result.language,
            "categories": topic_result.categories,
            "keywords": topic_result.keywords
        }

        # Add risk indicators based on topics
        high_risk_topics = ["politics", "controversial", "sensitive"]
        if any(topic in topic_result.primary_topic.lower() for topic in high_risk_topics):
            context["high_risk_topic"] = True
            context["moderation_note"] = "Content contains potentially sensitive topics"

        # Add content type specific notes
        if topic_result.content_type == "social_media":
            context["social_media_content"] = True
            context["moderation_note"] = "Social media style content detected"
        elif topic_result.content_type == "promotional":
            context["promotional_content"] = True
            context["moderation_note"] = "Promotional content detected"

        # Add language-specific handling
        if topic_result.language != "en":
            context["non_english_content"] = True
            context["moderation_note"] = f"Content in {topic_result.language} detected"

        return context


# Global topic extractor instance
_topic_extractor: Optional[TopicExtractor] = None


def get_topic_extractor() -> TopicExtractor:
    """Get global topic extractor instance."""
    global _topic_extractor
    if _topic_extractor is None:
        _topic_extractor = TopicExtractor()
    return _topic_extractor


def extract_content_topics(text: str) -> TopicResult:
    """
    Convenience function to extract topics from text.

    Args:
        text: Text to analyze

    Returns:
        TopicResult
    """
    extractor = get_topic_extractor()
    return extractor.extract_topics(text)
