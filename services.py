"""
Business logic services for FIST Content Moderation System.

This module contains the core business logic for content moderation,
including content piercing, AI integration, and decision analysis.
Enhanced with advanced text analysis capabilities.
"""
import random
import json
import logging
from typing import List, Optional, Dict, Any

from ai_connector import AIConnector
from config import Config
from cache import cache_manager
from monitoring import metrics_collector

# Import enhanced text analysis services
try:
    from services.sentiment_analyzer import get_sentiment_analyzer, SentimentResult
    from services.topic_extractor import get_topic_extractor, TopicResult
    from services.text_analyzer import get_text_analyzer, TextAnalysisResult
    from services.content_processor import get_content_processor, process_content_intelligently
    from services.threshold_manager import get_threshold_manager, make_adaptive_decision
    ENHANCED_ANALYSIS_AVAILABLE = True
    INTELLIGENT_PROCESSING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Enhanced text analysis not available: {e}")
    ENHANCED_ANALYSIS_AVAILABLE = False
    INTELLIGENT_PROCESSING_AVAILABLE = False


class ModerationService:
    """Service class for content moderation."""

    def __init__(self):
        """Initialize the moderation service."""
        self.ai_connector = AIConnector(Config.AI_API_KEY, Config.AI_BASE_URL)
        self.ai_connector.set_model(Config.AI_MODEL)

    def update_ai_config(self, api_key: str, base_url: str, model: str):
        """Update AI configuration and reinitialize connector."""
        self.ai_connector = AIConnector(api_key, base_url)
        self.ai_connector.set_model(model)

    def pierce_content(
        self,
        text: str,
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None
    ) -> tuple[str, float]:
        """Pierce content into pieces according to the rules."""
        words = text.split()
        if len(words) == 1 and len(text.strip()) > 10:
            words = list(text.strip())

        word_count = len(words)
        if percentages is None:
            percentages = Config.DEFAULT_PERCENTAGES
        if thresholds is None:
            thresholds = Config.DEFAULT_THRESHOLDS

        percentage_index = 0
        for i, threshold in enumerate(thresholds):
            if word_count < threshold:
                break
            percentage_index = i + 1

        if percentage_index < len(percentages):
            percentage = percentages[percentage_index]
        else:
            percentage = percentages[-1]

        words_to_keep = int(word_count * percentage)
        if word_count > words_to_keep:
            max_start_index = word_count - words_to_keep
            start_index = random.randint(0, max_start_index)
        else:
            start_index = 0

        selected_words = words[start_index:start_index + words_to_keep]
        if len(words) > 1 and all(len(word) == 1 for word in words[:10]):
            pierced_content = ''.join(selected_words)
        else:
            pierced_content = ' '.join(selected_words)

        return pierced_content, percentage

    def pierce_content_intelligently(
        self,
        text: str,
        target_percentage: Optional[float] = None
    ) -> tuple[str, float]:
        """
        Pierce content using intelligent content processing.

        Args:
            text: Text to process
            target_percentage: Target percentage of content to extract

        Returns:
            Tuple of (processed_content, actual_percentage)
        """
        if not INTELLIGENT_PROCESSING_AVAILABLE:
            # Fallback to traditional piercing
            return self.pierce_content(text)

        try:
            # Use intelligent content processor
            processed_content = process_content_intelligently(text, target_percentage)

            # Calculate actual percentage
            original_words = len(text.split())
            processed_words = len(processed_content.split())
            actual_percentage = processed_words / original_words if original_words > 0 else 0.0

            return processed_content, actual_percentage

        except Exception as e:
            logging.warning(f"Intelligent processing failed, falling back to traditional: {e}")
            return self.pierce_content(text)

    def check_content_with_ai(self, text: str) -> Dict[str, Any]:
        """Check content with AI."""
        return self.ai_connector.moderate_content(text)

    def analyze_result(
        self,
        ai_result: Dict[str, Any],
        probability_thresholds: Optional[Dict[str, int]] = None
    ) -> Dict[str, str]:
        """Analyze the AI moderation result and make the final decision."""
        if probability_thresholds is None:
            probability_thresholds = Config.DEFAULT_PROBABILITY_THRESHOLDS

        inappropriate_prob = ai_result.get("inappropriate_probability", 50)
        ai_reason = ai_result.get("reason", "No reason provided")

        if inappropriate_prob <= probability_thresholds["low"]:
            final_decision = "A"
            reason = f"Low risk ({inappropriate_prob}%): {ai_reason}"
        elif inappropriate_prob <= probability_thresholds["high"]:
            final_decision = "M"
            reason = f"Medium risk ({inappropriate_prob}%): {ai_reason}"
        else:
            final_decision = "R"
            reason = f"High risk ({inappropriate_prob}%): {ai_reason}"

        return {"final_decision": final_decision, "reason": reason}

    def analyze_result_enhanced(
        self,
        ai_result: Dict[str, Any],
        probability_thresholds: Optional[Dict[str, int]] = None,
        enhanced_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Analyze AI result with enhanced context from text analysis.

        Args:
            ai_result: AI moderation result
            probability_thresholds: Custom probability thresholds
            enhanced_analysis: Enhanced text analysis results

        Returns:
            Dictionary with final decision and reason
        """
        # Start with basic analysis
        basic_result = self.analyze_result(ai_result, probability_thresholds)

        if not enhanced_analysis:
            return basic_result

        # Extract enhanced context
        final_decision = basic_result["final_decision"]
        reason_parts = [basic_result["reason"]]

        # Adjust decision based on enhanced analysis
        inappropriate_prob = ai_result.get("inappropriate_probability", 0)

        # Sentiment-based adjustments
        if "sentiment_analysis" in enhanced_analysis:
            sentiment = enhanced_analysis["sentiment_analysis"]
            if sentiment["label"] == "negative" and sentiment["confidence"] > 0.8:
                if inappropriate_prob < 50:  # Boost negative sentiment content
                    reason_parts.append("Strong negative sentiment detected")
                    if final_decision == "A":
                        final_decision = "M"  # Escalate to manual review

        # Quality-based adjustments
        if "text_quality" in enhanced_analysis:
            quality = enhanced_analysis["text_quality"]

            # High spam probability
            if quality["spam_probability"] > Config.MAX_SPAM_PROBABILITY:
                reason_parts.append(f"High spam probability ({quality['spam_probability']:.2f})")
                if final_decision == "A":
                    final_decision = "M"  # Escalate to manual review

            # Low quality content
            if quality["quality_score"] < Config.MIN_QUALITY_SCORE:
                reason_parts.append(f"Low quality content ({quality['quality_score']:.2f})")
                if final_decision == "A" and inappropriate_prob > 30:
                    final_decision = "M"  # Escalate borderline low-quality content

        # Topic-based adjustments
        if "topic_extraction" in enhanced_analysis:
            topic = enhanced_analysis["topic_extraction"]

            # Check for sensitive topics
            sensitive_topics = ["politics", "controversial", "adult", "violence"]
            if any(sensitive in topic["primary_topic"].lower() for sensitive in sensitive_topics):
                reason_parts.append(f"Sensitive topic detected: {topic['primary_topic']}")
                if final_decision == "A" and inappropriate_prob > 20:
                    final_decision = "M"  # Lower threshold for sensitive topics

            # Language-specific handling
            if topic["language"] != "en":
                reason_parts.append(f"Non-English content ({topic['language']})")
                # Could add language-specific rules here

        # Combine all reasons
        enhanced_reason = "; ".join(reason_parts)

        return {"final_decision": final_decision, "reason": enhanced_reason}

    def analyze_result_adaptive(
        self,
        ai_result: Dict[str, Any],
        enhanced_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Analyze AI result using adaptive threshold management.

        Args:
            ai_result: AI moderation result
            enhanced_analysis: Enhanced text analysis results

        Returns:
            Dictionary with final decision and reason
        """
        if not INTELLIGENT_PROCESSING_AVAILABLE:
            # Fallback to enhanced analysis
            return self.analyze_result_enhanced(ai_result, None, enhanced_analysis)

        try:
            # Convert AI probability to score (0-1)
            inappropriate_prob = ai_result.get("inappropriate_probability", 0)
            ai_score = inappropriate_prob / 100.0  # Convert percentage to 0-1 scale

            # Make adaptive decision
            decision_result = make_adaptive_decision(ai_score, enhanced_analysis or {})

            # Format reason with adaptive context
            reason_parts = [
                f"AI score: {ai_score:.3f}",
                f"Threshold: {decision_result.threshold_used:.3f}",
                decision_result.reasoning
            ]

            # Add adjustment information
            if decision_result.adjustments_applied:
                adjustments_summary = f"Applied {len(decision_result.adjustments_applied)} context adjustments"
                reason_parts.append(adjustments_summary)

            return {
                "final_decision": decision_result.decision,
                "reason": "; ".join(reason_parts),
                "confidence": decision_result.confidence,
                "adaptive_context": {
                    "threshold_used": decision_result.threshold_used,
                    "threshold_type": decision_result.threshold_type.value,
                    "adjustments_count": len(decision_result.adjustments_applied),
                    "context_factors": [adj.factor.value for adj in decision_result.adjustments_applied]
                }
            }

        except Exception as e:
            logging.warning(f"Adaptive analysis failed, falling back to enhanced: {e}")
            return self.analyze_result_enhanced(ai_result, None, enhanced_analysis)

    def perform_enhanced_analysis(self, content: str) -> Dict[str, Any]:
        """
        Perform enhanced text analysis including sentiment, topics, and quality.

        Args:
            content: Text content to analyze

        Returns:
            Dictionary with enhanced analysis results
        """
        enhanced_results = {}

        if not ENHANCED_ANALYSIS_AVAILABLE:
            return enhanced_results

        try:
            # Sentiment Analysis
            if Config.ENABLE_SENTIMENT_ANALYSIS:
                sentiment_analyzer = get_sentiment_analyzer()
                sentiment_result = sentiment_analyzer.analyze_sentiment(content)
                enhanced_results["sentiment_analysis"] = {
                    "score": sentiment_result.score,
                    "confidence": sentiment_result.confidence,
                    "label": sentiment_result.label,
                    "backend": sentiment_result.backend,
                    "context": sentiment_analyzer.get_sentiment_context(sentiment_result)
                }

            # Topic Extraction
            if Config.ENABLE_TOPIC_EXTRACTION:
                topic_extractor = get_topic_extractor()
                topic_result = topic_extractor.extract_topics(content)
                enhanced_results["topic_extraction"] = {
                    "primary_topic": topic_result.primary_topic,
                    "topic_confidence": topic_result.topic_confidence,
                    "all_topics": [{"topic": topic, "confidence": conf} for topic, conf in topic_result.all_topics],
                    "keywords": topic_result.keywords,
                    "categories": topic_result.categories,
                    "content_type": topic_result.content_type,
                    "language": topic_result.language,
                    "context": topic_extractor.get_topic_context(topic_result)
                }

            # Text Quality Analysis
            if Config.ENABLE_TEXT_ANALYSIS:
                text_analyzer = get_text_analyzer()
                analysis_result = text_analyzer.analyze_text(content)
                enhanced_results["text_quality"] = {
                    "quality_score": analysis_result.quality.quality_score,
                    "readability_level": analysis_result.readability.readability_level,
                    "complexity_score": analysis_result.complexity.complexity_score,
                    "spam_probability": analysis_result.quality.spam_probability,
                    "spelling_errors": analysis_result.quality.spelling_errors,
                    "analysis_confidence": analysis_result.analysis_confidence,
                    "context": text_analyzer.get_analysis_context(analysis_result)
                }

                # Store detailed analysis for potential use
                enhanced_results["detailed_analysis"] = {
                    "readability": {
                        "flesch_kincaid_grade": analysis_result.readability.flesch_kincaid_grade,
                        "flesch_reading_ease": analysis_result.readability.flesch_reading_ease,
                        "readability_level": analysis_result.readability.readability_level
                    },
                    "complexity": {
                        "lexical_diversity": analysis_result.complexity.lexical_diversity,
                        "average_word_length": analysis_result.complexity.average_word_length,
                        "average_sentence_length": analysis_result.complexity.average_sentence_length,
                        "complexity_score": analysis_result.complexity.complexity_score
                    },
                    "linguistic": {
                        "pos_tags": analysis_result.linguistic.pos_tags,
                        "named_entities": analysis_result.linguistic.named_entities,
                        "linguistic_complexity": analysis_result.linguistic.linguistic_complexity,
                        "formality_score": analysis_result.linguistic.formality_score
                    }
                }

        except Exception as e:
            logging.error(f"Enhanced analysis failed: {e}")
            enhanced_results["analysis_error"] = str(e)

        return enhanced_results

    def enhance_ai_prompt(self, content: str, enhanced_analysis: Dict[str, Any]) -> str:
        """
        Enhance AI prompt with context from advanced text analysis.

        Args:
            content: Original content
            enhanced_analysis: Results from enhanced analysis

        Returns:
            Enhanced content with analysis context
        """
        if not enhanced_analysis:
            return content

        context_parts = []

        # Add sentiment context
        if "sentiment_analysis" in enhanced_analysis:
            sentiment = enhanced_analysis["sentiment_analysis"]
            context_parts.append(f"[SENTIMENT: {sentiment['label']} ({sentiment['score']:.2f})]")

        # Add topic context
        if "topic_extraction" in enhanced_analysis:
            topic = enhanced_analysis["topic_extraction"]
            context_parts.append(f"[TOPIC: {topic['primary_topic']}]")
            if topic["categories"]:
                context_parts.append(f"[CATEGORIES: {', '.join(topic['categories'][:2])}]")

        # Add quality context
        if "text_quality" in enhanced_analysis:
            quality = enhanced_analysis["text_quality"]
            if quality["spam_probability"] > 0.5:
                context_parts.append(f"[HIGH_SPAM_RISK: {quality['spam_probability']:.2f}]")
            if quality["quality_score"] < 0.3:
                context_parts.append("[LOW_QUALITY]")

        # Combine context with content
        if context_parts:
            context_str = " ".join(context_parts)
            return f"{context_str}\n\n{content}"

        return content

    def moderate_content(
        self,
        content: str,
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None,
        enable_enhanced_analysis: bool = True,
        use_intelligent_processing: bool = True
    ) -> Dict[str, Any]:
        """Perform complete content moderation with enhanced analysis and caching support."""
        # Check cache first
        cached_result = cache_manager.get_cached_result(
            content, percentages, thresholds, probability_thresholds
        )

        if cached_result:
            metrics_collector.record_cache_operation("get", "hit")
            # Return cached result with original content for consistency
            cached_result["original_content"] = content
            return cached_result

        metrics_collector.record_cache_operation("get", "miss")

        # Process content normally
        words = content.split()
        if len(words) == 1 and len(content.strip()) > 10:
            words = list(content.strip())
        word_count = len(words)

        # Perform enhanced analysis if enabled
        enhanced_analysis = {}
        if enable_enhanced_analysis and ENHANCED_ANALYSIS_AVAILABLE:
            enhanced_analysis = self.perform_enhanced_analysis(content)

        # Pierce content using intelligent processing if available
        if use_intelligent_processing and INTELLIGENT_PROCESSING_AVAILABLE:
            # Calculate target percentage from traditional logic
            if percentages is None:
                percentages = Config.DEFAULT_PERCENTAGES
            if thresholds is None:
                thresholds = Config.DEFAULT_THRESHOLDS

            percentage_index = 0
            for i, threshold in enumerate(thresholds):
                if word_count < threshold:
                    break
                percentage_index = i + 1

            if percentage_index < len(percentages):
                target_percentage = percentages[percentage_index]
            else:
                target_percentage = percentages[-1]

            # Use intelligent processing
            pierced_content, percentage_used = self.pierce_content_intelligently(content, target_percentage)
        else:
            # Use traditional processing
            pierced_content, percentage_used = self.pierce_content(content, percentages, thresholds)

        # Enhance pierced content with analysis context for AI
        ai_input_content = pierced_content
        if enhanced_analysis:
            ai_input_content = self.enhance_ai_prompt(pierced_content, enhanced_analysis)

        # Get AI result
        ai_result = self.check_content_with_ai(ai_input_content)

        # Analyze result with enhanced context and adaptive thresholds
        if use_intelligent_processing and INTELLIGENT_PROCESSING_AVAILABLE:
            analysis = self.analyze_result_adaptive(ai_result, enhanced_analysis)
        else:
            analysis = self.analyze_result_enhanced(ai_result, probability_thresholds, enhanced_analysis)

        result = {
            "original_content": content,
            "pierced_content": pierced_content,
            "word_count": word_count,
            "percentage_used": percentage_used,
            "ai_result": ai_result,
            "final_decision": analysis["final_decision"],
            "reason": analysis["reason"],
            "enhanced_analysis": enhanced_analysis,
            "analysis_confidence": enhanced_analysis.get("text_quality", {}).get("analysis_confidence", 1.0)
        }

        # Cache the result
        cache_manager.cache_result(
            content, result, percentages, thresholds, probability_thresholds
        )

        # Record AI call metrics
        metrics_collector.record_ai_call("success")

        return result
