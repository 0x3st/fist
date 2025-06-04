"""
Language Detection Service for FIST Content Moderation System.

This module provides comprehensive language detection and processing capabilities including:
- Automatic language detection with confidence scoring
- Mixed-language content handling
- Language-specific processing pipelines
- Support for 20+ languages with specialized Chinese processing
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict

from config import Config


class SupportedLanguage(Enum):
    """Comprehensive list of supported languages."""
    ENGLISH = "en"
    CHINESE_SIMPLIFIED = "zh-cn"
    CHINESE_TRADITIONAL = "zh-tw"
    JAPANESE = "ja"
    KOREAN = "ko"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    ARABIC = "ar"
    HINDI = "hi"
    THAI = "th"
    VIETNAMESE = "vi"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"
    POLISH = "pl"
    CZECH = "cs"
    HUNGARIAN = "hu"
    TURKISH = "tr"
    GREEK = "el"
    HEBREW = "he"
    UNKNOWN = "unknown"


class LanguageFamily(Enum):
    """Language family classifications."""
    INDO_EUROPEAN = "indo_european"
    SINO_TIBETAN = "sino_tibetan"
    AFRO_ASIATIC = "afro_asiatic"
    ALTAIC = "altaic"
    AUSTROASIATIC = "austroasiatic"
    TAI_KADAI = "tai_kadai"
    UNKNOWN = "unknown"


@dataclass
class LanguageDetectionResult:
    """Comprehensive language detection result."""
    primary_language: SupportedLanguage
    confidence: float
    all_languages: List[Tuple[SupportedLanguage, float]]
    is_mixed_language: bool
    language_distribution: Dict[str, float]
    script_type: str
    language_family: LanguageFamily
    processing_notes: List[str] = field(default_factory=list)


@dataclass
class LanguageProcessingResult:
    """Result of language-specific processing."""
    original_text: str
    processed_text: str
    language: SupportedLanguage
    tokens: List[str]
    sentences: List[str]
    word_count: int
    character_count: int
    processing_method: str
    quality_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedLanguageDetector:
    """Advanced language detection with multiple detection methods."""
    
    def __init__(self):
        """Initialize the language detector."""
        self.logger = logging.getLogger(__name__)
        
        # Language family mappings
        self.language_families = {
            SupportedLanguage.ENGLISH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.SPANISH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.FRENCH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.GERMAN: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.ITALIAN: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.PORTUGUESE: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.RUSSIAN: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.HINDI: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.DUTCH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.SWEDISH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.NORWEGIAN: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.DANISH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.POLISH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.CZECH: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.GREEK: LanguageFamily.INDO_EUROPEAN,
            SupportedLanguage.CHINESE_SIMPLIFIED: LanguageFamily.SINO_TIBETAN,
            SupportedLanguage.CHINESE_TRADITIONAL: LanguageFamily.SINO_TIBETAN,
            SupportedLanguage.ARABIC: LanguageFamily.AFRO_ASIATIC,
            SupportedLanguage.HEBREW: LanguageFamily.AFRO_ASIATIC,
            SupportedLanguage.JAPANESE: LanguageFamily.ALTAIC,
            SupportedLanguage.KOREAN: LanguageFamily.ALTAIC,
            SupportedLanguage.TURKISH: LanguageFamily.ALTAIC,
            SupportedLanguage.VIETNAMESE: LanguageFamily.AUSTROASIATIC,
            SupportedLanguage.THAI: LanguageFamily.TAI_KADAI,
        }
        
        # Character-based language detection patterns
        self.language_patterns = {
            SupportedLanguage.CHINESE_SIMPLIFIED: [
                r'[\u4e00-\u9fff]',  # CJK Unified Ideographs
                r'[\u3400-\u4dbf]',  # CJK Extension A
            ],
            SupportedLanguage.CHINESE_TRADITIONAL: [
                r'[\u4e00-\u9fff]',  # CJK Unified Ideographs
                r'[\uf900-\ufaff]',  # CJK Compatibility Ideographs
            ],
            SupportedLanguage.JAPANESE: [
                r'[\u3040-\u309f]',  # Hiragana
                r'[\u30a0-\u30ff]',  # Katakana
                r'[\u4e00-\u9fff]',  # Kanji
            ],
            SupportedLanguage.KOREAN: [
                r'[\uac00-\ud7af]',  # Hangul Syllables
                r'[\u1100-\u11ff]',  # Hangul Jamo
            ],
            SupportedLanguage.ARABIC: [
                r'[\u0600-\u06ff]',  # Arabic
                r'[\u0750-\u077f]',  # Arabic Supplement
            ],
            SupportedLanguage.HEBREW: [
                r'[\u0590-\u05ff]',  # Hebrew
            ],
            SupportedLanguage.RUSSIAN: [
                r'[\u0400-\u04ff]',  # Cyrillic
            ],
            SupportedLanguage.GREEK: [
                r'[\u0370-\u03ff]',  # Greek and Coptic
            ],
            SupportedLanguage.THAI: [
                r'[\u0e00-\u0e7f]',  # Thai
            ],
            SupportedLanguage.HINDI: [
                r'[\u0900-\u097f]',  # Devanagari
            ],
        }
        
        # Common words for statistical detection
        self.common_words = {
            SupportedLanguage.ENGLISH: {
                'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
                'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'
            },
            SupportedLanguage.SPANISH: {
                'de', 'la', 'que', 'el', 'en', 'y', 'a', 'es', 'se', 'no',
                'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al'
            },
            SupportedLanguage.FRENCH: {
                'de', 'le', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir',
                'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se'
            },
            SupportedLanguage.GERMAN: {
                'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich',
                'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als'
            },
            SupportedLanguage.ITALIAN: {
                'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'il',
                'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'e', 'che'
            },
            SupportedLanguage.PORTUGUESE: {
                'de', 'a', 'o', 'e', 'do', 'da', 'em', 'um', 'para', 'é',
                'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as'
            },
            SupportedLanguage.RUSSIAN: {
                'в', 'и', 'не', 'на', 'я', 'быть', 'тот', 'он', 'оно', 'она',
                'они', 'с', 'а', 'как', 'это', 'все', 'что', 'за', 'из', 'к'
            },
            SupportedLanguage.DUTCH: {
                'de', 'van', 'het', 'een', 'en', 'in', 'te', 'dat', 'op', 'voor',
                'met', 'als', 'zijn', 'er', 'maar', 'om', 'door', 'over', 'ze', 'bij'
            },
            SupportedLanguage.CHINESE_SIMPLIFIED: {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
                '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去'
            },
        }
        
        # Initialize external libraries if available
        self._init_external_libraries()
        
        self.logger.info("Advanced language detector initialized")
    
    def _init_external_libraries(self):
        """Initialize external language detection libraries."""
        # Try to import langdetect
        try:
            import langdetect
            self.langdetect_available = True
            self.logger.info("langdetect library available")
        except ImportError:
            self.langdetect_available = False
            self.logger.warning("langdetect library not available")
        
        # Try to import polyglot
        try:
            from polyglot.detect import Detector
            self.polyglot_available = True
            self.logger.info("polyglot library available")
        except ImportError:
            self.polyglot_available = False
            self.logger.warning("polyglot library not available")
    
    def detect_language_character_based(self, text: str) -> LanguageDetectionResult:
        """Detect language using character-based patterns."""
        language_scores = {}
        processing_notes = []
        
        # Score based on character patterns
        for language, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text))
                score += matches
            
            if score > 0:
                language_scores[language] = score / len(text)
        
        # Score based on common words
        words = text.lower().split()
        for language, common_words in self.common_words.items():
            if language not in language_scores:
                language_scores[language] = 0
            
            word_matches = sum(1 for word in words if word in common_words)
            if word_matches > 0:
                language_scores[language] += word_matches / len(words)
        
        # Default to English if no patterns match
        if not language_scores:
            language_scores[SupportedLanguage.ENGLISH] = 0.5
            processing_notes.append("Defaulted to English - no patterns matched")
        
        # Sort by score
        sorted_languages = sorted(language_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_language = sorted_languages[0][0]
        confidence = min(1.0, sorted_languages[0][1] * 2)  # Scale confidence
        
        # Check for mixed language content
        significant_languages = [lang for lang, score in sorted_languages if score > 0.1]
        is_mixed = len(significant_languages) > 1
        
        # Determine script type
        script_type = self._determine_script_type(text)
        
        # Get language family
        language_family = self.language_families.get(primary_language, LanguageFamily.UNKNOWN)
        
        processing_notes.append("Used character-based detection")
        
        return LanguageDetectionResult(
            primary_language=primary_language,
            confidence=confidence,
            all_languages=sorted_languages,
            is_mixed_language=is_mixed,
            language_distribution={lang.value: score for lang, score in sorted_languages},
            script_type=script_type,
            language_family=language_family,
            processing_notes=processing_notes
        )
    
    def detect_language_statistical(self, text: str) -> LanguageDetectionResult:
        """Detect language using statistical methods with external libraries."""
        processing_notes = []
        
        if self.langdetect_available:
            try:
                import langdetect
                from langdetect import detect_langs
                
                # Get language probabilities
                lang_probs = detect_langs(text)
                
                # Convert to our format
                all_languages = []
                language_distribution = {}
                
                for lang_prob in lang_probs:
                    lang_code = lang_prob.lang
                    confidence = lang_prob.prob
                    
                    # Map to our supported languages
                    supported_lang = self._map_language_code(lang_code)
                    all_languages.append((supported_lang, confidence))
                    language_distribution[supported_lang.value] = confidence
                
                primary_language = all_languages[0][0] if all_languages else SupportedLanguage.ENGLISH
                primary_confidence = all_languages[0][1] if all_languages else 0.5
                
                # Check for mixed language
                significant_languages = [lang for lang, conf in all_languages if conf > 0.1]
                is_mixed = len(significant_languages) > 1
                
                # Determine script type and language family
                script_type = self._determine_script_type(text)
                language_family = self.language_families.get(primary_language, LanguageFamily.UNKNOWN)
                
                processing_notes.append("Used langdetect statistical detection")
                
                return LanguageDetectionResult(
                    primary_language=primary_language,
                    confidence=primary_confidence,
                    all_languages=all_languages,
                    is_mixed_language=is_mixed,
                    language_distribution=language_distribution,
                    script_type=script_type,
                    language_family=language_family,
                    processing_notes=processing_notes
                )
                
            except Exception as e:
                self.logger.warning(f"Statistical language detection failed: {e}")
                processing_notes.append(f"Statistical detection failed: {e}")
        
        # Fallback to character-based detection
        result = self.detect_language_character_based(text)
        result.processing_notes.extend(processing_notes)
        return result
    
    def _map_language_code(self, lang_code: str) -> SupportedLanguage:
        """Map external library language codes to our supported languages."""
        mapping = {
            'en': SupportedLanguage.ENGLISH,
            'zh-cn': SupportedLanguage.CHINESE_SIMPLIFIED,
            'zh': SupportedLanguage.CHINESE_SIMPLIFIED,
            'zh-tw': SupportedLanguage.CHINESE_TRADITIONAL,
            'ja': SupportedLanguage.JAPANESE,
            'ko': SupportedLanguage.KOREAN,
            'es': SupportedLanguage.SPANISH,
            'fr': SupportedLanguage.FRENCH,
            'de': SupportedLanguage.GERMAN,
            'it': SupportedLanguage.ITALIAN,
            'pt': SupportedLanguage.PORTUGUESE,
            'ru': SupportedLanguage.RUSSIAN,
            'ar': SupportedLanguage.ARABIC,
            'hi': SupportedLanguage.HINDI,
            'th': SupportedLanguage.THAI,
            'vi': SupportedLanguage.VIETNAMESE,
            'nl': SupportedLanguage.DUTCH,
            'sv': SupportedLanguage.SWEDISH,
            'no': SupportedLanguage.NORWEGIAN,
            'da': SupportedLanguage.DANISH,
            'fi': SupportedLanguage.FINNISH,
            'pl': SupportedLanguage.POLISH,
            'cs': SupportedLanguage.CZECH,
            'hu': SupportedLanguage.HUNGARIAN,
            'tr': SupportedLanguage.TURKISH,
            'el': SupportedLanguage.GREEK,
            'he': SupportedLanguage.HEBREW,
        }
        
        return mapping.get(lang_code, SupportedLanguage.UNKNOWN)
    
    def _determine_script_type(self, text: str) -> str:
        """Determine the writing script type of the text."""
        script_patterns = {
            'latin': r'[a-zA-Z]',
            'chinese': r'[\u4e00-\u9fff]',
            'japanese': r'[\u3040-\u309f\u30a0-\u30ff]',
            'korean': r'[\uac00-\ud7af]',
            'cyrillic': r'[\u0400-\u04ff]',
            'arabic': r'[\u0600-\u06ff]',
            'hebrew': r'[\u0590-\u05ff]',
            'thai': r'[\u0e00-\u0e7f]',
            'devanagari': r'[\u0900-\u097f]',
            'greek': r'[\u0370-\u03ff]',
        }
        
        script_scores = {}
        for script, pattern in script_patterns.items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                script_scores[script] = matches / len(text)
        
        if not script_scores:
            return 'unknown'
        
        # Check for mixed scripts
        if len(script_scores) > 1:
            max_score = max(script_scores.values())
            if max_score < 0.7:  # No dominant script
                return 'mixed'
        
        return max(script_scores.keys(), key=lambda k: script_scores[k])
    
    def detect_language(self, text: str, method: str = "auto") -> LanguageDetectionResult:
        """
        Detect language using specified method.
        
        Args:
            text: Text to analyze
            method: Detection method ('auto', 'statistical', 'character')
            
        Returns:
            Language detection result
        """
        if method == "statistical" or (method == "auto" and self.langdetect_available):
            return self.detect_language_statistical(text)
        else:
            return self.detect_language_character_based(text)


class ChineseTextProcessor:
    """Specialized processor for Chinese text."""
    
    def __init__(self):
        """Initialize Chinese text processor."""
        self.logger = logging.getLogger(__name__)
        
        # Try to import jieba for Chinese segmentation
        try:
            import jieba
            self.jieba = jieba
            self.jieba_available = True
            self.logger.info("jieba Chinese segmentation available")
        except ImportError:
            self.jieba_available = False
            self.logger.warning("jieba not available, using basic Chinese processing")
        
        # Traditional to Simplified Chinese mapping (basic)
        self.trad_to_simp = {
            '繁': '繁', '體': '体', '中': '中', '文': '文',
            '處': '处', '理': '理', '測': '测', '試': '试'
        }
    
    def segment_chinese_text(self, text: str) -> List[str]:
        """Segment Chinese text into words."""
        if self.jieba_available:
            return list(self.jieba.cut(text))
        else:
            # Basic character-level segmentation
            return list(text)
    
    def convert_traditional_to_simplified(self, text: str) -> str:
        """Convert Traditional Chinese to Simplified Chinese (basic)."""
        result = text
        for trad, simp in self.trad_to_simp.items():
            result = result.replace(trad, simp)
        return result
    
    def process_chinese_text(self, text: str, variant: SupportedLanguage) -> LanguageProcessingResult:
        """Process Chinese text with segmentation and normalization."""
        processed_text = text
        processing_method = "basic"
        
        # Convert Traditional to Simplified if needed
        if variant == SupportedLanguage.CHINESE_TRADITIONAL:
            processed_text = self.convert_traditional_to_simplified(text)
            processing_method += "_trad_to_simp"
        
        # Segment text
        tokens = self.segment_chinese_text(processed_text)
        
        # Basic sentence segmentation (split on Chinese punctuation)
        sentences = re.split(r'[。！？；]', processed_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate quality score (basic)
        quality_score = min(1.0, len(tokens) / max(1, len(processed_text)) * 10)
        
        if self.jieba_available:
            processing_method += "_jieba"
        
        return LanguageProcessingResult(
            original_text=text,
            processed_text=processed_text,
            language=variant,
            tokens=tokens,
            sentences=sentences,
            word_count=len(tokens),
            character_count=len(processed_text),
            processing_method=processing_method,
            quality_score=quality_score,
            metadata={
                'variant': variant.value,
                'segmentation_method': 'jieba' if self.jieba_available else 'character',
                'conversion_applied': variant == SupportedLanguage.CHINESE_TRADITIONAL
            }
        )


class MultiLanguageProcessor:
    """Comprehensive multi-language text processor."""
    
    def __init__(self):
        """Initialize multi-language processor."""
        self.logger = logging.getLogger(__name__)
        self.language_detector = AdvancedLanguageDetector()
        self.chinese_processor = ChineseTextProcessor()
        
        # Try to initialize spaCy models
        self.spacy_models = {}
        self._init_spacy_models()
        
        self.logger.info("Multi-language processor initialized")
    
    def _init_spacy_models(self):
        """Initialize available spaCy models."""
        model_mappings = {
            SupportedLanguage.ENGLISH: 'en_core_web_sm',
            SupportedLanguage.CHINESE_SIMPLIFIED: 'zh_core_web_sm',
            SupportedLanguage.SPANISH: 'es_core_news_sm',
            SupportedLanguage.FRENCH: 'fr_core_news_sm',
            SupportedLanguage.GERMAN: 'de_core_news_sm',
            SupportedLanguage.ITALIAN: 'it_core_news_sm',
            SupportedLanguage.PORTUGUESE: 'pt_core_news_sm',
            SupportedLanguage.DUTCH: 'nl_core_news_sm',
        }
        
        try:
            import spacy
            for language, model_name in model_mappings.items():
                try:
                    self.spacy_models[language] = spacy.load(model_name)
                    self.logger.info(f"Loaded spaCy model for {language.value}")
                except OSError:
                    self.logger.warning(f"spaCy model {model_name} not available for {language.value}")
        except ImportError:
            self.logger.warning("spaCy not available")
    
    def process_text_by_language(self, text: str, language: SupportedLanguage) -> LanguageProcessingResult:
        """Process text using language-specific methods."""
        # Special handling for Chinese
        if language in [SupportedLanguage.CHINESE_SIMPLIFIED, SupportedLanguage.CHINESE_TRADITIONAL]:
            return self.chinese_processor.process_chinese_text(text, language)
        
        # Use spaCy if available
        if language in self.spacy_models:
            return self._process_with_spacy(text, language)
        
        # Fallback to basic processing
        return self._process_basic(text, language)
    
    def _process_with_spacy(self, text: str, language: SupportedLanguage) -> LanguageProcessingResult:
        """Process text using spaCy."""
        nlp = self.spacy_models[language]
        doc = nlp(text)
        
        tokens = [token.text for token in doc if not token.is_space]
        sentences = [sent.text.strip() for sent in doc.sents]
        
        # Calculate quality score based on linguistic features
        quality_factors = []
        
        # Token-to-character ratio
        if len(text) > 0:
            quality_factors.append(len(tokens) / len(text))
        
        # Sentence structure
        if len(tokens) > 0:
            avg_sentence_length = len(tokens) / max(1, len(sentences))
            quality_factors.append(min(1.0, avg_sentence_length / 20))  # Normalize to 20 words
        
        # Named entity recognition
        entities = [ent.text for ent in doc.ents]
        if len(tokens) > 0:
            entity_ratio = len(entities) / len(tokens)
            quality_factors.append(min(1.0, entity_ratio * 10))
        
        quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
        
        return LanguageProcessingResult(
            original_text=text,
            processed_text=text,
            language=language,
            tokens=tokens,
            sentences=sentences,
            word_count=len(tokens),
            character_count=len(text),
            processing_method="spacy",
            quality_score=quality_score,
            metadata={
                'entities': entities,
                'pos_tags': [token.pos_ for token in doc],
                'lemmas': [token.lemma_ for token in doc if not token.is_space]
            }
        )
    
    def _process_basic(self, text: str, language: SupportedLanguage) -> LanguageProcessingResult:
        """Basic text processing without external libraries."""
        # Simple tokenization
        tokens = re.findall(r'\b\w+\b', text)
        
        # Simple sentence segmentation
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Basic quality score
        quality_score = 0.5
        if len(text) > 0:
            # Word density
            word_density = len(tokens) / len(text.split())
            quality_score = min(1.0, word_density)
        
        return LanguageProcessingResult(
            original_text=text,
            processed_text=text,
            language=language,
            tokens=tokens,
            sentences=sentences,
            word_count=len(tokens),
            character_count=len(text),
            processing_method="basic",
            quality_score=quality_score,
            metadata={'method': 'regex_based'}
        )
    
    def analyze_text(self, text: str) -> Tuple[LanguageDetectionResult, LanguageProcessingResult]:
        """
        Perform comprehensive language analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (language_detection_result, processing_result)
        """
        # Detect language
        detection_result = self.language_detector.detect_language(text)
        
        # Process text using detected language
        processing_result = self.process_text_by_language(text, detection_result.primary_language)
        
        return detection_result, processing_result


# Global instances
_language_detector: Optional[AdvancedLanguageDetector] = None
_multi_language_processor: Optional[MultiLanguageProcessor] = None


def get_language_detector() -> AdvancedLanguageDetector:
    """Get global language detector instance."""
    global _language_detector
    if _language_detector is None:
        _language_detector = AdvancedLanguageDetector()
    return _language_detector


def get_multi_language_processor() -> MultiLanguageProcessor:
    """Get global multi-language processor instance."""
    global _multi_language_processor
    if _multi_language_processor is None:
        _multi_language_processor = MultiLanguageProcessor()
    return _multi_language_processor


def detect_and_process_text(text: str) -> Tuple[LanguageDetectionResult, LanguageProcessingResult]:
    """
    Convenience function to detect and process text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (detection_result, processing_result)
    """
    processor = get_multi_language_processor()
    return processor.analyze_text(text)
