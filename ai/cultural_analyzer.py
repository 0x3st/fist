"""
Cultural Context Awareness Service for FIST Content Moderation System.

This module provides cultural and regional context analysis including:
- Cultural sensitivity detection
- Regional compliance checking
- Localized moderation rules
- Cultural context-aware threshold adjustments
- Cross-cultural content analysis
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import json

from core.config import Config
from ai.language_detector import SupportedLanguage, LanguageFamily


class CulturalRegion(Enum):
    """Major cultural regions."""
    WESTERN = "western"
    EAST_ASIAN = "east_asian"
    SOUTHEAST_ASIAN = "southeast_asian"
    MIDDLE_EASTERN = "middle_eastern"
    SOUTH_ASIAN = "south_asian"
    AFRICAN = "african"
    LATIN_AMERICAN = "latin_american"
    SLAVIC = "slavic"
    NORDIC = "nordic"
    UNKNOWN = "unknown"


class CulturalSensitivity(Enum):
    """Cultural sensitivity levels."""
    VERY_HIGH = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    NEUTRAL = 1


class ContentCategory(Enum):
    """Content categories for cultural analysis."""
    RELIGIOUS = "religious"
    POLITICAL = "political"
    CULTURAL_TRADITION = "cultural_tradition"
    SOCIAL_NORM = "social_norm"
    HISTORICAL = "historical"
    COMMERCIAL = "commercial"
    ENTERTAINMENT = "entertainment"
    EDUCATIONAL = "educational"
    PERSONAL = "personal"
    UNKNOWN = "unknown"


@dataclass
class CulturalIndicator:
    """Individual cultural indicator."""
    indicator_type: str
    value: str
    confidence: float
    region: CulturalRegion
    sensitivity: CulturalSensitivity
    context: str = ""


@dataclass
class CulturalAnalysisResult:
    """Result of cultural context analysis."""
    primary_region: CulturalRegion
    detected_regions: List[Tuple[CulturalRegion, float]]
    cultural_indicators: List[CulturalIndicator]
    content_categories: List[Tuple[ContentCategory, float]]
    sensitivity_level: CulturalSensitivity
    cultural_conflicts: List[str]
    localization_notes: List[str]
    compliance_warnings: List[str]
    recommended_adjustments: Dict[str, Any]
    analysis_confidence: float


@dataclass
class RegionalModerationRules:
    """Regional-specific moderation rules."""
    region: CulturalRegion
    threshold_adjustments: Dict[str, float]
    prohibited_content: List[str]
    sensitive_topics: List[str]
    cultural_exceptions: List[str]
    compliance_requirements: List[str]


class CulturalContextAnalyzer:
    """Advanced cultural context analyzer."""

    def __init__(self):
        """Initialize cultural context analyzer."""
        self.logger = logging.getLogger(__name__)

        # Language to region mapping
        self.language_region_mapping = {
            SupportedLanguage.ENGLISH: [CulturalRegion.WESTERN, CulturalRegion.SOUTH_ASIAN],
            SupportedLanguage.CHINESE_SIMPLIFIED: [CulturalRegion.EAST_ASIAN],
            SupportedLanguage.CHINESE_TRADITIONAL: [CulturalRegion.EAST_ASIAN],
            SupportedLanguage.JAPANESE: [CulturalRegion.EAST_ASIAN],
            SupportedLanguage.KOREAN: [CulturalRegion.EAST_ASIAN],
            SupportedLanguage.SPANISH: [CulturalRegion.LATIN_AMERICAN, CulturalRegion.WESTERN],
            SupportedLanguage.FRENCH: [CulturalRegion.WESTERN, CulturalRegion.AFRICAN],
            SupportedLanguage.GERMAN: [CulturalRegion.WESTERN],
            SupportedLanguage.ITALIAN: [CulturalRegion.WESTERN],
            SupportedLanguage.PORTUGUESE: [CulturalRegion.LATIN_AMERICAN, CulturalRegion.WESTERN],
            SupportedLanguage.RUSSIAN: [CulturalRegion.SLAVIC],
            SupportedLanguage.ARABIC: [CulturalRegion.MIDDLE_EASTERN, CulturalRegion.AFRICAN],
            SupportedLanguage.HINDI: [CulturalRegion.SOUTH_ASIAN],
            SupportedLanguage.THAI: [CulturalRegion.SOUTHEAST_ASIAN],
            SupportedLanguage.VIETNAMESE: [CulturalRegion.SOUTHEAST_ASIAN],
            SupportedLanguage.DUTCH: [CulturalRegion.WESTERN],
            SupportedLanguage.SWEDISH: [CulturalRegion.NORDIC],
            SupportedLanguage.NORWEGIAN: [CulturalRegion.NORDIC],
            SupportedLanguage.DANISH: [CulturalRegion.NORDIC],
            SupportedLanguage.FINNISH: [CulturalRegion.NORDIC],
            SupportedLanguage.POLISH: [CulturalRegion.SLAVIC],
            SupportedLanguage.CZECH: [CulturalRegion.SLAVIC],
            SupportedLanguage.TURKISH: [CulturalRegion.MIDDLE_EASTERN],
            SupportedLanguage.GREEK: [CulturalRegion.WESTERN],
            SupportedLanguage.HEBREW: [CulturalRegion.MIDDLE_EASTERN],
        }

        # Cultural indicators by region
        self.cultural_indicators = {
            CulturalRegion.EAST_ASIAN: {
                'festivals': [
                    '春节', '中秋节', '端午节', '清明节', '国庆节', '元宵节',
                    '桜祭り', '正月', 'お盆', '七夕', '成人の日',
                    '추석', '설날', '어린이날', '한글날', '광복절'
                ],
                'concepts': [
                    '面子', '关系', '孝顺', '和谐', '中庸', '礼仪',
                    '和', '恥', '義理', '本音', '建前', '空気',
                    '정', '한', '체면', '눈치', '우리', '효도'
                ],
                'places': [
                    '北京', '上海', '广州', '深圳', '香港', '台北',
                    '東京', '大阪', '京都', '富士山', '神社', '寺',
                    '서울', '부산', '제주도', '경복궁', '한강'
                ],
                'food': [
                    '饺子', '月饼', '粽子', '火锅', '茶', '白酒',
                    '寿司', 'ラーメン', '天ぷら', '味噌', '日本酒',
                    '김치', '불고기', '비빔밥', '소주', '한정식'
                ]
            },
            CulturalRegion.MIDDLE_EASTERN: {
                'religious': [
                    'الله', 'محمد', 'القرآن', 'الصلاة', 'الحج', 'رمضان',
                    'عيد الفطر', 'عيد الأضحى', 'الجمعة', 'المسجد'
                ],
                'concepts': [
                    'الشرف', 'الكرامة', 'الضيافة', 'العائلة', 'التقاليد',
                    'الاحترام', 'الحلال', 'الحرام', 'الصبر'
                ],
                'places': [
                    'مكة', 'المدينة', 'القدس', 'دمشق', 'بغداد', 'القاهرة',
                    'الرياض', 'دبي', 'الدوحة', 'عمان'
                ]
            },
            CulturalRegion.WESTERN: {
                'holidays': [
                    'christmas', 'easter', 'thanksgiving', 'halloween',
                    'valentine', 'new year', 'independence day'
                ],
                'concepts': [
                    'freedom', 'democracy', 'individual rights', 'privacy',
                    'equality', 'justice', 'liberty', 'human rights'
                ],
                'places': [
                    'washington', 'london', 'paris', 'berlin', 'rome',
                    'madrid', 'amsterdam', 'stockholm', 'oslo'
                ]
            },
            CulturalRegion.SOUTH_ASIAN: {
                'religious': [
                    'हिंदू', 'बुद्ध', 'गुरु', 'मंदिर', 'गुरुद्वारा', 'मस्जिद',
                    'दिवाली', 'होली', 'दशहरा', 'ईद', 'गुरुपुर्ब'
                ],
                'concepts': [
                    'धर्म', 'कर्म', 'अहिंसा', 'सत्य', 'परिवार', 'सम्मान',
                    'आतिथ्य', 'गुरु', 'शिष्य', 'संस्कार'
                ],
                'places': [
                    'दिल्ली', 'मुंबई', 'कोलकाता', 'चेन्नई', 'बेंगलुरु',
                    'वाराणसी', 'अमृतसर', 'हरिद्वार', 'ऋषिकेश'
                ]
            }
        }

        # Sensitive topics by region
        self.sensitive_topics = {
            CulturalRegion.EAST_ASIAN: {
                'political': [
                    '台湾独立', '西藏独立', '新疆', '香港独立', '天安门',
                    '法轮功', '达赖喇嘛', '六四', '文革', '大跃进',
                    '独岛', '竹岛', '慰安妇', '靖国神社', '南京大屠杀'
                ],
                'social': [
                    '一胎政策', '户口制度', '社会信用', '网络审查',
                    '部落差别', '在日朝鲜人', '同和问题'
                ]
            },
            CulturalRegion.MIDDLE_EASTERN: {
                'religious': [
                    'blasphemy', 'apostasy', 'religious conversion',
                    'interfaith marriage', 'religious criticism'
                ],
                'political': [
                    'israel palestine', 'kurdish independence', 'sectarian conflict',
                    'arab spring', 'regime criticism'
                ],
                'social': [
                    'women rights', 'lgbt rights', 'alcohol', 'gambling',
                    'honor killing', 'forced marriage'
                ]
            },
            CulturalRegion.WESTERN: {
                'political': [
                    'hate speech', 'extremism', 'terrorism', 'racism',
                    'discrimination', 'political violence'
                ],
                'social': [
                    'cultural appropriation', 'gender issues', 'immigration',
                    'religious freedom', 'free speech limits'
                ]
            }
        }

        # Regional moderation rules
        self.regional_rules = self._initialize_regional_rules()

        self.logger.info("Cultural context analyzer initialized")

    def _initialize_regional_rules(self) -> Dict[CulturalRegion, RegionalModerationRules]:
        """Initialize regional moderation rules."""
        rules = {}

        # East Asian rules
        rules[CulturalRegion.EAST_ASIAN] = RegionalModerationRules(
            region=CulturalRegion.EAST_ASIAN,
            threshold_adjustments={
                'political_content': 0.3,  # Lower threshold (more strict)
                'religious_content': 0.1,
                'historical_content': 0.2,
                'social_criticism': 0.2
            },
            prohibited_content=[
                'political_dissent', 'territorial_disputes', 'historical_revisionism',
                'government_criticism', 'separatist_content'
            ],
            sensitive_topics=[
                'taiwan_independence', 'tibet_independence', 'hong_kong_independence',
                'tiananmen_square', 'falun_gong', 'dalai_lama'
            ],
            cultural_exceptions=[
                'traditional_festivals', 'cultural_practices', 'family_values'
            ],
            compliance_requirements=[
                'content_filtering', 'keyword_blocking', 'user_identification'
            ]
        )

        # Middle Eastern rules
        rules[CulturalRegion.MIDDLE_EASTERN] = RegionalModerationRules(
            region=CulturalRegion.MIDDLE_EASTERN,
            threshold_adjustments={
                'religious_content': 0.1,  # Very strict
                'blasphemy': 0.0,  # Zero tolerance
                'adult_content': 0.1,
                'alcohol_gambling': 0.2
            },
            prohibited_content=[
                'blasphemy', 'religious_mockery', 'adult_content',
                'alcohol_promotion', 'gambling_promotion'
            ],
            sensitive_topics=[
                'religious_conversion', 'interfaith_relations', 'womens_rights',
                'lgbt_content', 'political_criticism'
            ],
            cultural_exceptions=[
                'religious_education', 'cultural_traditions', 'family_values'
            ],
            compliance_requirements=[
                'religious_compliance', 'cultural_sensitivity', 'family_protection'
            ]
        )

        # Western rules
        rules[CulturalRegion.WESTERN] = RegionalModerationRules(
            region=CulturalRegion.WESTERN,
            threshold_adjustments={
                'hate_speech': 0.2,
                'discrimination': 0.2,
                'violence_incitement': 0.1,
                'misinformation': 0.3
            },
            prohibited_content=[
                'hate_speech', 'discrimination', 'violence_incitement',
                'terrorist_content', 'child_exploitation'
            ],
            sensitive_topics=[
                'racial_issues', 'gender_issues', 'immigration',
                'political_extremism', 'conspiracy_theories'
            ],
            cultural_exceptions=[
                'free_speech', 'artistic_expression', 'academic_discussion'
            ],
            compliance_requirements=[
                'gdpr_compliance', 'hate_speech_laws', 'child_protection'
            ]
        )

        return rules

    def detect_cultural_indicators(self, text: str, language: SupportedLanguage) -> List[CulturalIndicator]:
        """Detect cultural indicators in text."""
        indicators = []
        text_lower = text.lower()

        # Get potential regions for this language
        potential_regions = self.language_region_mapping.get(language, [CulturalRegion.UNKNOWN])

        for region in potential_regions:
            if region in self.cultural_indicators:
                region_indicators = self.cultural_indicators[region]

                for category, items in region_indicators.items():
                    for item in items:
                        # Check for exact matches and partial matches
                        item_lower = item.lower()
                        if item_lower in text_lower:
                            confidence = 1.0 if item_lower == text_lower else 0.8

                            # Determine sensitivity based on category and content
                            sensitivity = self._determine_sensitivity(category, item, region)

                            indicator = CulturalIndicator(
                                indicator_type=category,
                                value=item,
                                confidence=confidence,
                                region=region,
                                sensitivity=sensitivity,
                                context=f"Found in {category} category"
                            )
                            indicators.append(indicator)

        return indicators

    def _determine_sensitivity(self, category: str, item: str, region: CulturalRegion) -> CulturalSensitivity:
        """Determine sensitivity level for cultural indicator."""
        # Check if item is in sensitive topics
        if region in self.sensitive_topics:
            for topic_category, topics in self.sensitive_topics[region].items():
                if any(topic.lower() in item.lower() for topic in topics):
                    return CulturalSensitivity.VERY_HIGH

        # Category-based sensitivity
        sensitivity_mapping = {
            'religious': CulturalSensitivity.HIGH,
            'political': CulturalSensitivity.HIGH,
            'concepts': CulturalSensitivity.MEDIUM,
            'festivals': CulturalSensitivity.LOW,
            'food': CulturalSensitivity.LOW,
            'places': CulturalSensitivity.LOW
        }

        return sensitivity_mapping.get(category, CulturalSensitivity.NEUTRAL)

    def analyze_content_categories(self, text: str, cultural_indicators: List[CulturalIndicator]) -> List[Tuple[ContentCategory, float]]:
        """Analyze content categories based on text and cultural indicators."""
        category_scores = defaultdict(float)

        # Religious content detection
        religious_patterns = [
            r'\b(god|allah|buddha|jesus|christ|prayer|worship|temple|church|mosque|synagogue)\b',
            r'\b(الله|صلاة|مسجد|كنيسة|معبد|عبادة)\b',
            r'\b(神|佛|寺|庙|教堂|祈祷|崇拜)\b',
            r'\b(神|仏|寺|神社|教会|祈り|礼拝)\b'
        ]

        for pattern in religious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                category_scores[ContentCategory.RELIGIOUS] += 0.3

        # Political content detection
        political_patterns = [
            r'\b(government|politics|election|democracy|freedom|rights|protest|revolution)\b',
            r'\b(政府|政治|选举|民主|自由|权利|抗议|革命)\b',
            r'\b(政府|政治|選挙|民主|自由|権利|抗議|革命)\b'
        ]

        for pattern in political_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                category_scores[ContentCategory.POLITICAL] += 0.3

        # Commercial content detection
        commercial_patterns = [
            r'\b(buy|sell|price|discount|sale|shop|store|market|business|company)\b',
            r'\b(购买|销售|价格|折扣|商店|市场|公司|企业)\b',
            r'\b(買う|売る|価格|割引|店|市場|会社|企業)\b'
        ]

        for pattern in commercial_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                category_scores[ContentCategory.COMMERCIAL] += 0.3

        # Add scores from cultural indicators
        for indicator in cultural_indicators:
            if indicator.indicator_type == 'religious':
                category_scores[ContentCategory.RELIGIOUS] += 0.2
            elif indicator.indicator_type == 'political':
                category_scores[ContentCategory.POLITICAL] += 0.2
            elif indicator.indicator_type == 'festivals':
                category_scores[ContentCategory.CULTURAL_TRADITION] += 0.2

        # Normalize and sort scores
        if category_scores:
            max_score = max(category_scores.values())
            if max_score > 0:
                for category in category_scores:
                    category_scores[category] = min(1.0, category_scores[category] / max_score)

        # Return sorted categories
        return sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

    def detect_cultural_conflicts(self, cultural_indicators: List[CulturalIndicator]) -> List[str]:
        """Detect potential cultural conflicts in content."""
        conflicts = []

        # Group indicators by region
        region_indicators = defaultdict(list)
        for indicator in cultural_indicators:
            region_indicators[indicator.region].append(indicator)

        # Check for conflicting regions
        regions = list(region_indicators.keys())
        if len(regions) > 1:
            for i, region1 in enumerate(regions):
                for region2 in regions[i+1:]:
                    conflict = self._check_regional_conflict(region1, region2,
                                                           region_indicators[region1],
                                                           region_indicators[region2])
                    if conflict:
                        conflicts.append(conflict)

        # Check for sensitive topic combinations
        sensitive_indicators = [ind for ind in cultural_indicators
                              if ind.sensitivity in [CulturalSensitivity.HIGH, CulturalSensitivity.VERY_HIGH]]

        if len(sensitive_indicators) > 1:
            conflicts.append(f"Multiple sensitive topics detected: {', '.join([ind.value for ind in sensitive_indicators])}")

        return conflicts

    def _check_regional_conflict(self, region1: CulturalRegion, region2: CulturalRegion,
                               indicators1: List[CulturalIndicator],
                               indicators2: List[CulturalIndicator]) -> Optional[str]:
        """Check for conflicts between two regions."""
        # Known regional conflicts
        conflict_pairs = [
            (CulturalRegion.EAST_ASIAN, CulturalRegion.WESTERN),
            (CulturalRegion.MIDDLE_EASTERN, CulturalRegion.WESTERN),
        ]

        if (region1, region2) in conflict_pairs or (region2, region1) in conflict_pairs:
            # Check for specific conflicting indicators
            sensitive1 = [ind for ind in indicators1 if ind.sensitivity == CulturalSensitivity.VERY_HIGH]
            sensitive2 = [ind for ind in indicators2 if ind.sensitivity == CulturalSensitivity.VERY_HIGH]

            if sensitive1 and sensitive2:
                return f"Cultural conflict between {region1.value} and {region2.value} contexts"

        return None

    def get_regional_adjustments(self, primary_region: CulturalRegion,
                               content_categories: List[Tuple[ContentCategory, float]]) -> Dict[str, Any]:
        """Get recommended threshold adjustments for region."""
        adjustments = {}

        if primary_region in self.regional_rules:
            rules = self.regional_rules[primary_region]

            # Base threshold adjustments
            adjustments.update(rules.threshold_adjustments)

            # Category-specific adjustments
            for category, score in content_categories:
                if category == ContentCategory.RELIGIOUS and score > 0.5:
                    adjustments['religious_content'] = adjustments.get('religious_content', 0) - 0.1
                elif category == ContentCategory.POLITICAL and score > 0.5:
                    adjustments['political_content'] = adjustments.get('political_content', 0) - 0.1
                elif category == ContentCategory.COMMERCIAL and score > 0.3:
                    adjustments['commercial_content'] = adjustments.get('commercial_content', 0) + 0.1

        return adjustments

    def analyze_cultural_context(self, text: str, language: SupportedLanguage) -> CulturalAnalysisResult:
        """
        Perform comprehensive cultural context analysis.

        Args:
            text: Text to analyze
            language: Detected language

        Returns:
            Cultural analysis result
        """
        # Detect cultural indicators
        cultural_indicators = self.detect_cultural_indicators(text, language)

        # Determine primary region
        region_scores = defaultdict(float)
        for indicator in cultural_indicators:
            region_scores[indicator.region] += indicator.confidence

        # Add language-based region scoring
        potential_regions = self.language_region_mapping.get(language, [CulturalRegion.UNKNOWN])
        for region in potential_regions:
            region_scores[region] += 0.3  # Base score for language

        # Sort regions by score
        detected_regions = sorted(region_scores.items(), key=lambda x: x[1], reverse=True)
        primary_region = detected_regions[0][0] if detected_regions else CulturalRegion.UNKNOWN

        # Analyze content categories
        content_categories = self.analyze_content_categories(text, cultural_indicators)

        # Determine overall sensitivity level
        if cultural_indicators:
            max_sensitivity = max(ind.sensitivity for ind in cultural_indicators)
            sensitivity_level = max_sensitivity
        else:
            sensitivity_level = CulturalSensitivity.NEUTRAL

        # Detect cultural conflicts
        cultural_conflicts = self.detect_cultural_conflicts(cultural_indicators)

        # Generate localization notes
        localization_notes = []
        if primary_region != CulturalRegion.UNKNOWN:
            localization_notes.append(f"Content appears to be from {primary_region.value} cultural context")

        if len(detected_regions) > 1:
            localization_notes.append("Multi-cultural content detected")

        # Generate compliance warnings
        compliance_warnings = []
        if primary_region in self.regional_rules:
            rules = self.regional_rules[primary_region]
            for category, score in content_categories:
                if category.value in [topic.replace('_', ' ') for topic in rules.sensitive_topics]:
                    compliance_warnings.append(f"Content touches on sensitive topic for {primary_region.value}")

        # Get recommended adjustments
        recommended_adjustments = self.get_regional_adjustments(primary_region, content_categories)

        # Calculate analysis confidence
        analysis_confidence = 0.5  # Base confidence
        if cultural_indicators:
            avg_indicator_confidence = sum(ind.confidence for ind in cultural_indicators) / len(cultural_indicators)
            analysis_confidence = (analysis_confidence + avg_indicator_confidence) / 2

        return CulturalAnalysisResult(
            primary_region=primary_region,
            detected_regions=detected_regions,
            cultural_indicators=cultural_indicators,
            content_categories=content_categories,
            sensitivity_level=sensitivity_level,
            cultural_conflicts=cultural_conflicts,
            localization_notes=localization_notes,
            compliance_warnings=compliance_warnings,
            recommended_adjustments=recommended_adjustments,
            analysis_confidence=analysis_confidence
        )


# Global instance
_cultural_analyzer: Optional[CulturalContextAnalyzer] = None


def get_cultural_analyzer() -> CulturalContextAnalyzer:
    """Get global cultural analyzer instance."""
    global _cultural_analyzer
    if _cultural_analyzer is None:
        _cultural_analyzer = CulturalContextAnalyzer()
    return _cultural_analyzer


def analyze_cultural_context(text: str, language: SupportedLanguage) -> CulturalAnalysisResult:
    """
    Convenience function to analyze cultural context.

    Args:
        text: Text to analyze
        language: Detected language

    Returns:
        Cultural analysis result
    """
    analyzer = get_cultural_analyzer()
    return analyzer.analyze_cultural_context(text, language)
