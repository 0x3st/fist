"""
Multilingual Content Processing for FIST Content Moderation System.

This module provides advanced multilingual content processing capabilities including:
- Language detection and classification
- Cross-language content analysis
- Multilingual sentiment analysis
- Cultural context awareness
- Translation and normalization
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

from config import Config


class SupportedLanguage(Enum):
    """Supported languages for content processing."""
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
    UNKNOWN = "unknown"


class ContentScript(Enum):
    """Writing script types."""
    LATIN = "latin"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    KOREAN = "korean"
    CYRILLIC = "cyrillic"
    ARABIC = "arabic"
    DEVANAGARI = "devanagari"
    THAI = "thai"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    primary_language: SupportedLanguage
    confidence: float
    all_languages: List[Tuple[SupportedLanguage, float]]
    script_type: ContentScript
    is_multilingual: bool
    language_distribution: Dict[str, float] = field(default_factory=dict)


@dataclass
class MultilingualAnalysisResult:
    """Result of multilingual content analysis."""
    language_detection: LanguageDetectionResult
    normalized_content: str
    translated_content: Optional[str]
    cultural_context: Dict[str, Any]
    processing_notes: List[str]
    analysis_confidence: float


class MultilingualProcessor:
    """Advanced multilingual content processor."""
    
    def __init__(self):
        """Initialize the multilingual processor."""
        self.logger = logging.getLogger(__name__)
        
        # Language detection patterns
        self.language_patterns = {
            SupportedLanguage.CHINESE_SIMPLIFIED: [
                r'[\u4e00-\u9fff]',  # CJK Unified Ideographs
                r'[\u3400-\u4dbf]',  # CJK Extension A
            ],
            SupportedLanguage.CHINESE_TRADITIONAL: [
                r'[\u4e00-\u9fff]',  # CJK Unified Ideographs (overlap with simplified)
                r'[\uf900-\ufaff]',  # CJK Compatibility Ideographs
            ],
            SupportedLanguage.JAPANESE: [
                r'[\u3040-\u309f]',  # Hiragana
                r'[\u30a0-\u30ff]',  # Katakana
                r'[\u4e00-\u9fff]',  # Kanji (shared with Chinese)
            ],
            SupportedLanguage.KOREAN: [
                r'[\uac00-\ud7af]',  # Hangul Syllables
                r'[\u1100-\u11ff]',  # Hangul Jamo
            ],
            SupportedLanguage.ARABIC: [
                r'[\u0600-\u06ff]',  # Arabic
                r'[\u0750-\u077f]',  # Arabic Supplement
            ],
            SupportedLanguage.RUSSIAN: [
                r'[\u0400-\u04ff]',  # Cyrillic
            ],
            SupportedLanguage.HINDI: [
                r'[\u0900-\u097f]',  # Devanagari
            ],
            SupportedLanguage.THAI: [
                r'[\u0e00-\u0e7f]',  # Thai
            ],
            SupportedLanguage.VIETNAMESE: [
                r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
            ]
        }
        
        # Script detection patterns
        self.script_patterns = {
            ContentScript.CHINESE: r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]',
            ContentScript.JAPANESE: r'[\u3040-\u309f\u30a0-\u30ff]',
            ContentScript.KOREAN: r'[\uac00-\ud7af\u1100-\u11ff]',
            ContentScript.CYRILLIC: r'[\u0400-\u04ff]',
            ContentScript.ARABIC: r'[\u0600-\u06ff\u0750-\u077f]',
            ContentScript.DEVANAGARI: r'[\u0900-\u097f]',
            ContentScript.THAI: r'[\u0e00-\u0e7f]',
            ContentScript.LATIN: r'[a-zA-Z]',
        }
        
        # Language-specific stopwords (basic sets)
        self.stopwords = {
            SupportedLanguage.ENGLISH: {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
            },
            SupportedLanguage.CHINESE_SIMPLIFIED: {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很',
                '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '可以'
            },
            SupportedLanguage.JAPANESE: {
                'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ', 'ある', 'いる', 'する',
                'です', 'ます', 'だ', 'である', 'この', 'その', 'あの', 'どの', 'これ', 'それ', 'あれ', 'どれ'
            },
            SupportedLanguage.KOREAN: {
                '이', '가', '을', '를', '에', '에서', '로', '으로', '와', '과', '의', '도', '만', '부터', '까지',
                '는', '은', '한', '하다', '있다', '없다', '되다', '이다', '아니다', '그', '이', '저', '그것', '이것'
            },
            SupportedLanguage.SPANISH: {
                'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da',
                'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'pero', 'todo', 'esta'
            },
            SupportedLanguage.FRENCH: {
                'le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce',
                'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'en', 'une'
            },
            SupportedLanguage.GERMAN: {
                'der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für',
                'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus', 'er'
            },
            SupportedLanguage.RUSSIAN: {
                'в', 'и', 'не', 'на', 'я', 'быть', 'тот', 'он', 'оно', 'она', 'они', 'с', 'а', 'как', 'это',
                'все', 'что', 'за', 'из', 'к', 'по', 'до', 'от', 'у', 'о', 'для', 'при', 'со', 'без'
            },
            SupportedLanguage.ARABIC: {
                'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'كانت', 'يكون', 'تكون',
                'هو', 'هي', 'أن', 'إن', 'كل', 'بعض', 'غير', 'سوف', 'قد', 'لقد', 'منذ', 'حتى'
            }
        }
        
        # Cultural context indicators
        self.cultural_indicators = {
            'chinese_culture': [
                r'春节|中秋|端午|清明|国庆|中国|北京|上海|广州|深圳',
                r'人民币|元|RMB|CNY',
                r'微信|支付宝|淘宝|京东|百度|腾讯|阿里巴巴'
            ],
            'japanese_culture': [
                r'桜|寿司|忍者|侍|東京|大阪|京都|富士山',
                r'円|JPY|¥',
                r'ソニー|トヨタ|任天堂|ホンダ|パナソニック'
            ],
            'korean_culture': [
                r'김치|불고기|서울|부산|대구|광주|K-pop|한류',
                r'원|KRW|₩',
                r'삼성|LG|현대|기아|SK|롯데'
            ],
            'western_culture': [
                r'Christmas|Halloween|Thanksgiving|Easter|Valentine',
                r'USD|EUR|GBP|\$|€|£',
                r'Google|Apple|Microsoft|Amazon|Facebook|Netflix'
            ],
            'islamic_culture': [
                r'رمضان|عيد|حج|مكة|المدينة|الله|محمد|إسلام|مسلم',
                r'صلاة|زكاة|صوم|حج|شهادة',
                r'السعودية|الإمارات|قطر|الكويت|البحرين'
            ]
        }
        
        # Initialize external libraries if available
        self._init_external_libraries()
        
        self.logger.info("Multilingual processor initialized")
    
    def _init_external_libraries(self):
        """Initialize external libraries for enhanced language processing."""
        # Try to import language detection libraries
        try:
            import langdetect
            self.langdetect_available = True
            self.logger.info("langdetect library available")
        except ImportError:
            self.langdetect_available = False
            self.logger.warning("langdetect library not available")
        
        # Try to import translation libraries
        try:
            from googletrans import Translator
            self.translator = Translator()
            self.translation_available = True
            self.logger.info("Google Translate available")
        except ImportError:
            self.translation_available = False
            self.logger.warning("Google Translate not available")
        
        # Try to import advanced NLP libraries
        try:
            import polyglot
            self.polyglot_available = True
            self.logger.info("Polyglot library available")
        except ImportError:
            self.polyglot_available = False
            self.logger.warning("Polyglot library not available")
    
    def detect_script_type(self, text: str) -> ContentScript:
        """
        Detect the writing script type of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected script type
        """
        script_scores = {}
        
        for script, pattern in self.script_patterns.items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                script_scores[script] = matches / len(text)
        
        if not script_scores:
            return ContentScript.UNKNOWN
        
        # Check for mixed scripts
        if len(script_scores) > 1:
            max_score = max(script_scores.values())
            if max_score < 0.7:  # No dominant script
                return ContentScript.MIXED
        
        return max(script_scores.keys(), key=lambda k: script_scores[k])
    
    def detect_language_basic(self, text: str) -> LanguageDetectionResult:
        """
        Basic language detection using character patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language detection result
        """
        language_scores = {}
        
        # Score based on character patterns
        for language, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text))
                score += matches
            
            if score > 0:
                language_scores[language] = score / len(text)
        
        # Default to English if no patterns match
        if not language_scores:
            language_scores[SupportedLanguage.ENGLISH] = 1.0
        
        # Sort by score
        sorted_languages = sorted(language_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_language = sorted_languages[0][0]
        confidence = sorted_languages[0][1]
        
        # Detect script type
        script_type = self.detect_script_type(text)
        
        # Check if multilingual
        is_multilingual = len([score for score in language_scores.values() if score > 0.1]) > 1
        
        return LanguageDetectionResult(
            primary_language=primary_language,
            confidence=min(1.0, confidence * 10),  # Scale confidence
            all_languages=sorted_languages,
            script_type=script_type,
            is_multilingual=is_multilingual,
            language_distribution={lang.value: score for lang, score in sorted_languages}
        )
    
    def detect_language_advanced(self, text: str) -> LanguageDetectionResult:
        """
        Advanced language detection using external libraries.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language detection result
        """
        if not self.langdetect_available:
            return self.detect_language_basic(text)
        
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
            
            # Detect script type
            script_type = self.detect_script_type(text)
            
            # Check if multilingual
            is_multilingual = len([conf for _, conf in all_languages if conf > 0.1]) > 1
            
            return LanguageDetectionResult(
                primary_language=primary_language,
                confidence=primary_confidence,
                all_languages=all_languages,
                script_type=script_type,
                is_multilingual=is_multilingual,
                language_distribution=language_distribution
            )
            
        except Exception as e:
            self.logger.warning(f"Advanced language detection failed: {e}")
            return self.detect_language_basic(text)
    
    def _map_language_code(self, lang_code: str) -> SupportedLanguage:
        """Map language code to supported language."""
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
        }
        
        return mapping.get(lang_code, SupportedLanguage.UNKNOWN)
    
    def detect_cultural_context(self, text: str, language: SupportedLanguage) -> Dict[str, Any]:
        """
        Detect cultural context indicators in the text.
        
        Args:
            text: Text to analyze
            language: Detected language
            
        Returns:
            Cultural context information
        """
        cultural_context = {
            'detected_cultures': [],
            'cultural_confidence': 0.0,
            'cultural_indicators': [],
            'region_specific': False,
            'religious_content': False,
            'commercial_content': False
        }
        
        text_lower = text.lower()
        
        # Check for cultural indicators
        for culture, patterns in self.cultural_indicators.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    cultural_context['detected_cultures'].append(culture)
                    cultural_context['cultural_indicators'].extend(matches)
        
        # Remove duplicates
        cultural_context['detected_cultures'] = list(set(cultural_context['detected_cultures']))
        cultural_context['cultural_indicators'] = list(set(cultural_context['cultural_indicators']))
        
        # Calculate confidence
        if cultural_context['cultural_indicators']:
            cultural_context['cultural_confidence'] = min(1.0, len(cultural_context['cultural_indicators']) / 10)
        
        # Detect specific content types
        religious_patterns = [
            r'god|allah|buddha|jesus|christ|prayer|worship|temple|church|mosque|synagogue',
            r'الله|صلاة|مسجد|كنيسة|معبد|عبادة',
            r'神|佛|寺|庙|教堂|祈祷|崇拜',
            r'神|仏|寺|神社|教会|祈り|礼拝'
        ]
        
        for pattern in religious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                cultural_context['religious_content'] = True
                break
        
        # Detect commercial content
        commercial_patterns = [
            r'buy|sell|price|discount|sale|shop|store|market|business|company',
            r'购买|销售|价格|折扣|商店|市场|公司|企业',
            r'買う|売る|価格|割引|店|市場|会社|企業',
            r'구매|판매|가격|할인|상점|시장|회사|기업'
        ]
        
        for pattern in commercial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                cultural_context['commercial_content'] = True
                break
        
        return cultural_context
    
    def normalize_content(self, text: str, language: SupportedLanguage) -> str:
        """
        Normalize content based on language-specific rules.
        
        Args:
            text: Text to normalize
            language: Detected language
            
        Returns:
            Normalized text
        """
        normalized = text
        
        # Basic normalization
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        normalized = normalized.strip()
        
        # Language-specific normalization
        if language in [SupportedLanguage.CHINESE_SIMPLIFIED, SupportedLanguage.CHINESE_TRADITIONAL]:
            # Remove extra spaces around Chinese characters
            normalized = re.sub(r'(\u4e00-\u9fff)\s+(\u4e00-\u9fff)', r'\1\2', normalized)
            
        elif language == SupportedLanguage.JAPANESE:
            # Normalize Japanese spacing
            normalized = re.sub(r'(\u3040-\u309f|\u30a0-\u30ff|\u4e00-\u9fff)\s+(\u3040-\u309f|\u30a0-\u30ff|\u4e00-\u9fff)', r'\1\2', normalized)
            
        elif language == SupportedLanguage.KOREAN:
            # Normalize Korean spacing
            normalized = re.sub(r'(\uac00-\ud7af)\s+(\uac00-\ud7af)', r'\1\2', normalized)
            
        elif language == SupportedLanguage.ARABIC:
            # Normalize Arabic text direction and spacing
            normalized = re.sub(r'(\u0600-\u06ff)\s+(\u0600-\u06ff)', r'\1\2', normalized)
        
        return normalized
    
    def translate_content(self, text: str, target_language: str = "en") -> Optional[str]:
        """
        Translate content to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            
        Returns:
            Translated text or None if translation fails
        """
        if not self.translation_available:
            return None
        
        try:
            result = self.translator.translate(text, dest=target_language)
            return result.text
        except Exception as e:
            self.logger.warning(f"Translation failed: {e}")
            return None
    
    def process_multilingual_content(self, text: str) -> MultilingualAnalysisResult:
        """
        Perform comprehensive multilingual content analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Multilingual analysis result
        """
        processing_notes = []
        
        # Detect language
        if self.langdetect_available:
            language_detection = self.detect_language_advanced(text)
            processing_notes.append("Used advanced language detection")
        else:
            language_detection = self.detect_language_basic(text)
            processing_notes.append("Used basic language detection")
        
        # Normalize content
        normalized_content = self.normalize_content(text, language_detection.primary_language)
        processing_notes.append(f"Normalized for {language_detection.primary_language.value}")
        
        # Detect cultural context
        cultural_context = self.detect_cultural_context(text, language_detection.primary_language)
        
        # Translate if not English
        translated_content = None
        if language_detection.primary_language != SupportedLanguage.ENGLISH:
            translated_content = self.translate_content(text, "en")
            if translated_content:
                processing_notes.append("Translated to English")
            else:
                processing_notes.append("Translation not available")
        
        # Calculate analysis confidence
        analysis_confidence = language_detection.confidence
        if cultural_context['cultural_confidence'] > 0:
            analysis_confidence = (analysis_confidence + cultural_context['cultural_confidence']) / 2
        
        return MultilingualAnalysisResult(
            language_detection=language_detection,
            normalized_content=normalized_content,
            translated_content=translated_content,
            cultural_context=cultural_context,
            processing_notes=processing_notes,
            analysis_confidence=analysis_confidence
        )
    
    def get_language_specific_stopwords(self, language: SupportedLanguage) -> Set[str]:
        """Get stopwords for a specific language."""
        return self.stopwords.get(language, set())
    
    def is_content_appropriate_for_culture(self, text: str, target_culture: str) -> Tuple[bool, str]:
        """
        Check if content is appropriate for a specific cultural context.
        
        Args:
            text: Text to check
            target_culture: Target cultural context
            
        Returns:
            Tuple of (is_appropriate, reason)
        """
        # This is a simplified implementation
        # In practice, this would involve complex cultural sensitivity analysis
        
        cultural_context = self.detect_cultural_context(text, SupportedLanguage.ENGLISH)
        
        # Basic checks for cultural sensitivity
        sensitive_patterns = {
            'chinese_culture': [
                r'taiwan.*independent|tibet.*independent|hong kong.*independent',
                r'tiananmen|falun gong|dalai lama'
            ],
            'islamic_culture': [
                r'pork|alcohol|gambling|interest|usury',
                r'inappropriate religious references'
            ],
            'western_culture': [
                r'extreme political views|hate speech|discrimination'
            ]
        }
        
        if target_culture in sensitive_patterns:
            for pattern in sensitive_patterns[target_culture]:
                if re.search(pattern, text, re.IGNORECASE):
                    return False, f"Content may be sensitive for {target_culture}"
        
        return True, "Content appears appropriate"


# Global multilingual processor instance
_multilingual_processor: Optional[MultilingualProcessor] = None


def get_multilingual_processor() -> MultilingualProcessor:
    """Get global multilingual processor instance."""
    global _multilingual_processor
    if _multilingual_processor is None:
        _multilingual_processor = MultilingualProcessor()
    return _multilingual_processor


def process_multilingual_content(text: str) -> MultilingualAnalysisResult:
    """
    Convenience function to process multilingual content.
    
    Args:
        text: Text to process
        
    Returns:
        Multilingual analysis result
    """
    processor = get_multilingual_processor()
    return processor.process_multilingual_content(text)
