"""
Advanced Text Analysis Service for FIST Content Moderation System.

This module provides comprehensive text analysis including readability,
complexity metrics, quality assessment, and linguistic features.
"""
import logging
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import string

# Import NLP libraries with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available")


@dataclass
class ReadabilityMetrics:
    """Readability analysis results."""
    flesch_kincaid_grade: float
    flesch_reading_ease: float
    gunning_fog_index: float
    automated_readability_index: float
    coleman_liau_index: float
    readability_level: str  # "elementary", "middle", "high", "college", "graduate"


@dataclass
class ComplexityMetrics:
    """Text complexity analysis results."""
    lexical_diversity: float  # Type-token ratio
    average_word_length: float
    average_sentence_length: float
    syllable_complexity: float
    punctuation_density: float
    capitalization_ratio: float
    complexity_score: float  # Overall complexity (0-1)


@dataclass
class QualityMetrics:
    """Text quality assessment results."""
    spelling_errors: int
    grammar_score: float  # 0-1, higher is better
    coherence_score: float  # 0-1, higher is better
    spam_probability: float  # 0-1, higher means more likely spam
    duplicate_content_ratio: float  # 0-1, ratio of repeated content
    quality_score: float  # Overall quality (0-1)


@dataclass
class LinguisticFeatures:
    """Linguistic feature analysis results."""
    pos_tags: Dict[str, int]  # Part-of-speech tag counts
    named_entities: List[Dict[str, Any]]
    dependency_patterns: List[str]
    linguistic_complexity: float
    formality_score: float  # 0-1, higher is more formal


@dataclass
class TextAnalysisResult:
    """Comprehensive text analysis result."""
    readability: ReadabilityMetrics
    complexity: ComplexityMetrics
    quality: QualityMetrics
    linguistic: LinguisticFeatures
    word_count: int
    sentence_count: int
    paragraph_count: int
    character_count: int
    analysis_confidence: float


class TextAnalyzer:
    """Advanced text analysis service."""

    def __init__(self):
        """Initialize text analyzer."""
        self.logger = logging.getLogger(__name__)

        # Initialize NLP components
        self._init_spacy()
        self._init_nltk()

        # Spam detection patterns
        self.spam_patterns = [
            r'\b(buy now|act fast|limited time|urgent|click here)\b',
            r'\b(free|win|winner|congratulations|prize)\b',
            r'\$\d+',
            r'\b(call now|don\'t wait|hurry)\b',
            r'[A-Z]{3,}',  # Excessive caps
            r'!{2,}',  # Multiple exclamation marks
            r'\b(viagra|casino|lottery|inheritance)\b'
        ]

        # Quality indicators
        self.quality_indicators = {
            'positive': [
                r'\b(analysis|research|study|evidence|data)\b',
                r'\b(therefore|however|furthermore|moreover)\b',
                r'\b(according to|based on|research shows)\b'
            ],
            'negative': [
                r'\b(omg|lol|wtf|lmao)\b',
                r'[.]{3,}',  # Excessive dots
                r'[?!]{2,}',  # Multiple punctuation
                r'\b(ur|u|r|2|4)\b'  # Text speak
            ]
        }

        self.logger.info("Text analyzer initialized")

    def _init_spacy(self):
        """Initialize spaCy NLP pipeline."""
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("spaCy model loaded successfully")
            except OSError:
                try:
                    from spacy.lang.en import English
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

        if NLTK_AVAILABLE:
            try:
                # Try to use NLTK data if already available, don't download
                try:
                    # Test if data is already available
                    self.stop_words = set(stopwords.words('english'))
                    self.logger.info("NLTK initialized with existing data")
                except LookupError:
                    # Data not available, use basic fallback
                    self.logger.warning("NLTK data not found, using basic stopwords")
                    self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])

            except Exception as e:
                self.logger.error(f"Failed to initialize NLTK: {e}")
                # Use basic fallback
                self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])

    def analyze_text(self, text: str) -> TextAnalysisResult:
        """
        Perform comprehensive text analysis.

        Args:
            text: Text to analyze

        Returns:
            TextAnalysisResult with comprehensive analysis
        """
        if not text or not text.strip():
            return self._empty_result()

        try:
            # Basic text statistics
            word_count = len(text.split())
            sentence_count = len(self._get_sentences(text))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            character_count = len(text)

            # Perform different types of analysis
            readability = self._analyze_readability(text, word_count, sentence_count)
            complexity = self._analyze_complexity(text, word_count, sentence_count)
            quality = self._analyze_quality(text, word_count)
            linguistic = self._analyze_linguistic_features(text)

            # Calculate overall analysis confidence
            confidence = self._calculate_confidence(text, word_count, sentence_count)

            return TextAnalysisResult(
                readability=readability,
                complexity=complexity,
                quality=quality,
                linguistic=linguistic,
                word_count=word_count,
                sentence_count=sentence_count,
                paragraph_count=paragraph_count,
                character_count=character_count,
                analysis_confidence=confidence
            )

        except Exception as e:
            self.logger.error(f"Text analysis failed: {e}")
            return self._empty_result()

    def _empty_result(self) -> TextAnalysisResult:
        """Return empty analysis result."""
        return TextAnalysisResult(
            readability=ReadabilityMetrics(0, 0, 0, 0, 0, "unknown"),
            complexity=ComplexityMetrics(0, 0, 0, 0, 0, 0, 0),
            quality=QualityMetrics(0, 0, 0, 0, 0, 0),
            linguistic=LinguisticFeatures({}, [], [], 0, 0),
            word_count=0,
            sentence_count=0,
            paragraph_count=0,
            character_count=0,
            analysis_confidence=0.0
        )

    def _get_sentences(self, text: str) -> List[str]:
        """Get sentences from text."""
        if NLTK_AVAILABLE:
            try:
                return sent_tokenize(text)
            except:
                pass

        # Fallback: simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_words(self, text: str) -> List[str]:
        """Get words from text."""
        if NLTK_AVAILABLE:
            try:
                return word_tokenize(text)
            except:
                pass

        # Fallback: simple word splitting
        return re.findall(r'\b\w+\b', text.lower())

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel

        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1

        return max(1, syllable_count)

    def _analyze_readability(self, text: str, word_count: int, sentence_count: int) -> ReadabilityMetrics:
        """Analyze text readability using various metrics."""
        if word_count == 0 or sentence_count == 0:
            return ReadabilityMetrics(0, 0, 0, 0, 0, "unknown")

        words = self._get_words(text)
        sentences = self._get_sentences(text)

        # Calculate basic metrics
        avg_sentence_length = word_count / sentence_count

        # Count syllables
        total_syllables = sum(self._count_syllables(word) for word in words)
        avg_syllables_per_word = total_syllables / word_count if word_count > 0 else 0

        # Count complex words (3+ syllables)
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
        complex_word_ratio = complex_words / word_count if word_count > 0 else 0

        # Flesch-Kincaid Grade Level
        fk_grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59

        # Flesch Reading Ease
        flesch_ease = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word

        # Gunning Fog Index
        gunning_fog = 0.4 * (avg_sentence_length + 100 * complex_word_ratio)

        # Automated Readability Index
        characters = sum(len(word) for word in words)
        ari = 4.71 * (characters / word_count) + 0.5 * avg_sentence_length - 21.43

        # Coleman-Liau Index
        avg_chars_per_100_words = (characters / word_count) * 100
        avg_sentences_per_100_words = (sentence_count / word_count) * 100
        coleman_liau = 0.0588 * avg_chars_per_100_words - 0.296 * avg_sentences_per_100_words - 15.8

        # Determine readability level
        avg_grade = (fk_grade + gunning_fog + ari + coleman_liau) / 4
        if avg_grade <= 6:
            level = "elementary"
        elif avg_grade <= 9:
            level = "middle"
        elif avg_grade <= 12:
            level = "high"
        elif avg_grade <= 16:
            level = "college"
        else:
            level = "graduate"

        return ReadabilityMetrics(
            flesch_kincaid_grade=max(0, fk_grade),
            flesch_reading_ease=max(0, min(100, flesch_ease)),
            gunning_fog_index=max(0, gunning_fog),
            automated_readability_index=max(0, ari),
            coleman_liau_index=max(0, coleman_liau),
            readability_level=level
        )

    def _analyze_complexity(self, text: str, word_count: int, sentence_count: int) -> ComplexityMetrics:
        """Analyze text complexity."""
        if word_count == 0:
            return ComplexityMetrics(0, 0, 0, 0, 0, 0, 0)

        words = self._get_words(text)

        # Lexical diversity (Type-Token Ratio)
        unique_words = len(set(words))
        lexical_diversity = unique_words / word_count if word_count > 0 else 0

        # Average word length
        avg_word_length = sum(len(word) for word in words) / word_count

        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # Syllable complexity
        total_syllables = sum(self._count_syllables(word) for word in words)
        syllable_complexity = total_syllables / word_count if word_count > 0 else 0

        # Punctuation density
        punctuation_count = sum(1 for char in text if char in string.punctuation)
        punctuation_density = punctuation_count / len(text) if len(text) > 0 else 0

        # Capitalization ratio
        capital_count = sum(1 for char in text if char.isupper())
        capitalization_ratio = capital_count / len(text) if len(text) > 0 else 0

        # Overall complexity score (0-1)
        complexity_factors = [
            min(1.0, lexical_diversity * 2),  # Higher diversity = more complex
            min(1.0, avg_word_length / 10),   # Longer words = more complex
            min(1.0, avg_sentence_length / 30), # Longer sentences = more complex
            min(1.0, syllable_complexity / 3),  # More syllables = more complex
        ]
        complexity_score = sum(complexity_factors) / len(complexity_factors)

        return ComplexityMetrics(
            lexical_diversity=lexical_diversity,
            average_word_length=avg_word_length,
            average_sentence_length=avg_sentence_length,
            syllable_complexity=syllable_complexity,
            punctuation_density=punctuation_density,
            capitalization_ratio=capitalization_ratio,
            complexity_score=complexity_score
        )

    def _analyze_quality(self, text: str, word_count: int) -> QualityMetrics:
        """Analyze text quality."""
        if word_count == 0:
            return QualityMetrics(0, 0, 0, 0, 0, 0)

        # Spelling errors (simple heuristic)
        words = self._get_words(text)
        potential_errors = 0
        for word in words:
            # Very basic spelling check - words with unusual patterns
            if len(word) > 2 and (
                word.count(word[0]) > len(word) * 0.5 or  # Repeated characters
                not any(c in 'aeiou' for c in word.lower()) or  # No vowels
                len(set(word)) == 1  # All same character
            ):
                potential_errors += 1

        spelling_errors = potential_errors

        # Grammar score (heuristic based on sentence structure)
        sentences = self._get_sentences(text)
        grammar_score = 1.0

        for sentence in sentences:
            sentence_words = sentence.split()
            if len(sentence_words) > 0:
                # Check for basic grammar issues
                if not sentence[0].isupper():  # Should start with capital
                    grammar_score -= 0.1
                if len(sentence_words) > 50:  # Very long sentences
                    grammar_score -= 0.1
                if len(sentence_words) < 3:  # Very short sentences
                    grammar_score -= 0.05

        grammar_score = max(0, min(1, grammar_score))

        # Coherence score (based on word repetition and flow)
        word_freq = Counter(words)
        most_common_freq = word_freq.most_common(1)[0][1] if word_freq else 1
        coherence_score = min(1.0, most_common_freq / len(words) * 10) if words else 0

        # Spam probability
        spam_score = 0
        text_lower = text.lower()
        for pattern in self.spam_patterns:
            matches = len(re.findall(pattern, text_lower))
            spam_score += matches * 0.1

        spam_probability = min(1.0, spam_score)

        # Duplicate content ratio
        sentences_lower = [s.lower().strip() for s in sentences]
        unique_sentences = len(set(sentences_lower))
        total_sentences = len(sentences_lower)
        duplicate_ratio = 1 - (unique_sentences / total_sentences) if total_sentences > 0 else 0

        # Overall quality score
        quality_factors = [
            1 - (spelling_errors / word_count),  # Fewer errors = better quality
            grammar_score,
            coherence_score,
            1 - spam_probability,  # Less spam = better quality
            1 - duplicate_ratio    # Less duplication = better quality
        ]
        quality_score = sum(max(0, factor) for factor in quality_factors) / len(quality_factors)

        return QualityMetrics(
            spelling_errors=spelling_errors,
            grammar_score=grammar_score,
            coherence_score=coherence_score,
            spam_probability=spam_probability,
            duplicate_content_ratio=duplicate_ratio,
            quality_score=quality_score
        )

    def _analyze_linguistic_features(self, text: str) -> LinguisticFeatures:
        """Analyze linguistic features."""
        pos_tags = {}
        named_entities = []
        dependency_patterns = []
        linguistic_complexity = 0.0
        formality_score = 0.5

        try:
            if self.nlp:
                doc = self.nlp(text)

                # POS tags
                pos_counts = Counter([token.pos_ for token in doc])
                pos_tags = dict(pos_counts)

                # Named entities
                for ent in doc.ents:
                    named_entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })

                # Dependency patterns (simplified)
                dep_patterns = [token.dep_ for token in doc]
                dependency_patterns = list(set(dep_patterns))

                # Linguistic complexity based on POS diversity
                total_tokens = len([token for token in doc if not token.is_space])
                if total_tokens > 0:
                    pos_diversity = len(set(pos_tags.keys())) / 17  # 17 is typical number of POS tags
                    linguistic_complexity = min(1.0, pos_diversity)

                # Formality score based on POS patterns
                formal_indicators = pos_tags.get('NOUN', 0) + pos_tags.get('ADJ', 0)
                informal_indicators = pos_tags.get('PRON', 0) + pos_tags.get('INTJ', 0)
                total_indicators = formal_indicators + informal_indicators

                if total_indicators > 0:
                    formality_score = formal_indicators / total_indicators

            elif NLTK_AVAILABLE:
                # Fallback to NLTK
                words = self._get_words(text)
                try:
                    pos_tagged = nltk.pos_tag(words)
                    pos_counts = Counter([tag for _, tag in pos_tagged])
                    pos_tags = dict(pos_counts)

                    # Simple linguistic complexity
                    linguistic_complexity = len(set(pos_tags.keys())) / 36  # 36 is typical number of NLTK POS tags

                except:
                    pass

        except Exception as e:
            self.logger.error(f"Linguistic analysis failed: {e}")

        return LinguisticFeatures(
            pos_tags=pos_tags,
            named_entities=named_entities,
            dependency_patterns=dependency_patterns,
            linguistic_complexity=linguistic_complexity,
            formality_score=formality_score
        )

    def _calculate_confidence(self, text: str, word_count: int, sentence_count: int) -> float:
        """Calculate analysis confidence based on text characteristics."""
        confidence_factors = []

        # Word count factor
        if word_count >= 50:
            confidence_factors.append(1.0)
        elif word_count >= 20:
            confidence_factors.append(0.8)
        elif word_count >= 10:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)

        # Sentence count factor
        if sentence_count >= 3:
            confidence_factors.append(1.0)
        elif sentence_count >= 2:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)

        # Text structure factor
        if '\n' in text or '.' in text:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)

        # Language detection confidence
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text.replace(' ', ''))
        if total_chars > 0:
            english_ratio = english_chars / total_chars
            confidence_factors.append(english_ratio)

        return sum(confidence_factors) / len(confidence_factors)

    def get_analysis_context(self, analysis_result: TextAnalysisResult) -> Dict[str, Any]:
        """
        Get additional context for content moderation based on text analysis.

        Args:
            analysis_result: Text analysis result

        Returns:
            Dictionary with analysis context for moderation
        """
        context = {
            "word_count": analysis_result.word_count,
            "readability_level": analysis_result.readability.readability_level,
            "complexity_score": analysis_result.complexity.complexity_score,
            "quality_score": analysis_result.quality.quality_score,
            "spam_probability": analysis_result.quality.spam_probability,
            "analysis_confidence": analysis_result.analysis_confidence
        }

        # Add risk indicators
        if analysis_result.quality.spam_probability > 0.7:
            context["high_spam_risk"] = True
            context["moderation_note"] = "High spam probability detected"

        if analysis_result.quality.quality_score < 0.3:
            context["low_quality_content"] = True
            context["moderation_note"] = "Low quality content detected"

        if analysis_result.complexity.complexity_score > 0.8:
            context["high_complexity"] = True
            context["moderation_note"] = "Highly complex content"

        if analysis_result.word_count < 10:
            context["very_short_content"] = True
            context["moderation_note"] = "Very short content"

        # Add readability context
        if analysis_result.readability.readability_level in ["graduate", "college"]:
            context["high_readability_level"] = True
        elif analysis_result.readability.readability_level == "elementary":
            context["low_readability_level"] = True

        return context


# Global text analyzer instance
_text_analyzer: Optional[TextAnalyzer] = None


def get_text_analyzer() -> TextAnalyzer:
    """Get global text analyzer instance."""
    global _text_analyzer
    if _text_analyzer is None:
        _text_analyzer = TextAnalyzer()
    return _text_analyzer


def analyze_text_comprehensive(text: str) -> TextAnalysisResult:
    """
    Convenience function to perform comprehensive text analysis.

    Args:
        text: Text to analyze

    Returns:
        TextAnalysisResult
    """
    analyzer = get_text_analyzer()
    return analyzer.analyze_text(text)
