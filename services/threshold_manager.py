"""
Dynamic Threshold Management for FIST Content Moderation System.

This module provides adaptive threshold management that adjusts decision
thresholds based on content characteristics, context, and historical data.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from config import Config


class ThresholdType(Enum):
    """Types of thresholds."""
    REJECTION = "rejection"
    MANUAL_REVIEW = "manual_review"
    APPROVAL = "approval"


class ContextFactor(Enum):
    """Context factors that influence thresholds."""
    CONTENT_TYPE = "content_type"
    CONTENT_LENGTH = "content_length"
    SENTIMENT = "sentiment"
    TOPIC = "topic"
    LANGUAGE = "language"
    TIME_OF_DAY = "time_of_day"
    USER_HISTORY = "user_history"
    SYSTEM_LOAD = "system_load"


@dataclass
class ThresholdAdjustment:
    """Represents a threshold adjustment."""
    factor: ContextFactor
    condition: str
    adjustment: float
    reason: str
    confidence: float = 1.0


@dataclass
class AdaptiveThreshold:
    """Adaptive threshold configuration."""
    base_value: float
    min_value: float
    max_value: float
    adjustments: List[ThresholdAdjustment] = field(default_factory=list)
    current_value: float = 0.0
    last_updated: float = 0.0
    
    def __post_init__(self):
        if self.current_value == 0.0:
            self.current_value = self.base_value
        if self.last_updated == 0.0:
            self.last_updated = time.time()


@dataclass
class ThresholdContext:
    """Context information for threshold calculation."""
    content_type: str = "general"
    content_length: int = 0
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    primary_topic: str = "general"
    language: str = "en"
    time_of_day: int = 12  # Hour of day (0-23)
    user_risk_score: float = 0.5
    system_load: float = 0.5
    enhanced_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThresholdDecision:
    """Result of threshold-based decision making."""
    decision: str  # 'R', 'M', 'A'
    confidence: float
    threshold_used: float
    threshold_type: ThresholdType
    adjustments_applied: List[ThresholdAdjustment]
    context: ThresholdContext
    reasoning: str


class DynamicThresholdManager:
    """Manages adaptive thresholds for content moderation decisions."""
    
    def __init__(self):
        """Initialize the threshold manager."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize base thresholds from config
        self.thresholds = {
            ThresholdType.REJECTION: AdaptiveThreshold(
                base_value=Config.REJECTION_THRESHOLD,
                min_value=0.6,
                max_value=0.95,
                current_value=Config.REJECTION_THRESHOLD
            ),
            ThresholdType.MANUAL_REVIEW: AdaptiveThreshold(
                base_value=Config.MANUAL_REVIEW_THRESHOLD,
                min_value=0.3,
                max_value=0.8,
                current_value=Config.MANUAL_REVIEW_THRESHOLD
            )
        }
        
        # Historical data for learning
        self.decision_history = deque(maxlen=1000)  # Last 1000 decisions
        self.performance_metrics = {
            'accuracy': 0.0,
            'false_positives': 0,
            'false_negatives': 0,
            'total_decisions': 0
        }
        
        # Context-based adjustment rules
        self.adjustment_rules = self._initialize_adjustment_rules()
        
        # Time-based patterns
        self.time_patterns = defaultdict(list)
        
        self.logger.info("Dynamic threshold manager initialized")
    
    def _initialize_adjustment_rules(self) -> Dict[ContextFactor, List[ThresholdAdjustment]]:
        """Initialize context-based adjustment rules."""
        rules = {
            ContextFactor.CONTENT_TYPE: [
                ThresholdAdjustment(
                    ContextFactor.CONTENT_TYPE,
                    "social_media",
                    -0.1,  # More lenient for social media
                    "Social media content tends to be more casual"
                ),
                ThresholdAdjustment(
                    ContextFactor.CONTENT_TYPE,
                    "news_article",
                    0.05,  # Slightly stricter for news
                    "News articles should maintain higher standards"
                ),
                ThresholdAdjustment(
                    ContextFactor.CONTENT_TYPE,
                    "promotional",
                    0.15,  # Much stricter for promotional content
                    "Promotional content requires stricter moderation"
                ),
                ThresholdAdjustment(
                    ContextFactor.CONTENT_TYPE,
                    "technical",
                    -0.05,  # More lenient for technical content
                    "Technical content may use specialized language"
                )
            ],
            
            ContextFactor.CONTENT_LENGTH: [
                ThresholdAdjustment(
                    ContextFactor.CONTENT_LENGTH,
                    "very_short",  # < 20 words
                    0.1,  # Stricter for very short content
                    "Short content provides less context for analysis"
                ),
                ThresholdAdjustment(
                    ContextFactor.CONTENT_LENGTH,
                    "very_long",  # > 500 words
                    -0.05,  # More lenient for long content
                    "Long content provides more context for analysis"
                )
            ],
            
            ContextFactor.SENTIMENT: [
                ThresholdAdjustment(
                    ContextFactor.SENTIMENT,
                    "very_negative",  # sentiment < -0.7
                    0.2,  # Much stricter for very negative content
                    "Very negative sentiment increases moderation risk"
                ),
                ThresholdAdjustment(
                    ContextFactor.SENTIMENT,
                    "positive",  # sentiment > 0.3
                    -0.1,  # More lenient for positive content
                    "Positive sentiment reduces moderation risk"
                )
            ],
            
            ContextFactor.TOPIC: [
                ThresholdAdjustment(
                    ContextFactor.TOPIC,
                    "politics",
                    0.15,  # Stricter for political content
                    "Political content requires careful moderation"
                ),
                ThresholdAdjustment(
                    ContextFactor.TOPIC,
                    "health",
                    0.1,  # Stricter for health content
                    "Health information requires accuracy verification"
                ),
                ThresholdAdjustment(
                    ContextFactor.TOPIC,
                    "entertainment",
                    -0.05,  # More lenient for entertainment
                    "Entertainment content is generally less risky"
                )
            ],
            
            ContextFactor.LANGUAGE: [
                ThresholdAdjustment(
                    ContextFactor.LANGUAGE,
                    "non_english",
                    0.1,  # Stricter for non-English content
                    "Non-English content may require specialized review"
                )
            ],
            
            ContextFactor.TIME_OF_DAY: [
                ThresholdAdjustment(
                    ContextFactor.TIME_OF_DAY,
                    "night_hours",  # 22:00 - 06:00
                    0.05,  # Slightly stricter during night hours
                    "Limited moderation staff during night hours"
                ),
                ThresholdAdjustment(
                    ContextFactor.TIME_OF_DAY,
                    "peak_hours",  # 09:00 - 17:00
                    -0.05,  # More lenient during peak hours
                    "Full moderation staff available during peak hours"
                )
            ],
            
            ContextFactor.USER_HISTORY: [
                ThresholdAdjustment(
                    ContextFactor.USER_HISTORY,
                    "high_risk_user",  # user_risk_score > 0.7
                    0.2,  # Much stricter for high-risk users
                    "User has history of problematic content"
                ),
                ThresholdAdjustment(
                    ContextFactor.USER_HISTORY,
                    "trusted_user",  # user_risk_score < 0.3
                    -0.1,  # More lenient for trusted users
                    "User has good moderation history"
                )
            ],
            
            ContextFactor.SYSTEM_LOAD: [
                ThresholdAdjustment(
                    ContextFactor.SYSTEM_LOAD,
                    "high_load",  # system_load > 0.8
                    0.1,  # Stricter when system is under high load
                    "High system load requires more automated decisions"
                ),
                ThresholdAdjustment(
                    ContextFactor.SYSTEM_LOAD,
                    "low_load",  # system_load < 0.3
                    -0.05,  # More lenient when system load is low
                    "Low system load allows for more manual review"
                )
            ]
        }
        
        return rules
    
    def _evaluate_context_condition(self, condition: str, context: ThresholdContext) -> bool:
        """
        Evaluate if a context condition is met.
        
        Args:
            condition: Condition to evaluate
            context: Current context
            
        Returns:
            True if condition is met
        """
        # Content type conditions
        if condition == "social_media":
            return context.content_type == "social_media"
        elif condition == "news_article":
            return context.content_type == "news_article"
        elif condition == "promotional":
            return context.content_type == "promotional"
        elif condition == "technical":
            return context.content_type == "technical"
        
        # Content length conditions
        elif condition == "very_short":
            return context.content_length < 20
        elif condition == "very_long":
            return context.content_length > 500
        
        # Sentiment conditions
        elif condition == "very_negative":
            return context.sentiment_score < -0.7
        elif condition == "positive":
            return context.sentiment_score > 0.3
        
        # Topic conditions
        elif condition == "politics":
            return "politic" in context.primary_topic.lower()
        elif condition == "health":
            return "health" in context.primary_topic.lower() or "medical" in context.primary_topic.lower()
        elif condition == "entertainment":
            return "entertainment" in context.primary_topic.lower()
        
        # Language conditions
        elif condition == "non_english":
            return context.language != "en"
        
        # Time conditions
        elif condition == "night_hours":
            return context.time_of_day >= 22 or context.time_of_day <= 6
        elif condition == "peak_hours":
            return 9 <= context.time_of_day <= 17
        
        # User history conditions
        elif condition == "high_risk_user":
            return context.user_risk_score > 0.7
        elif condition == "trusted_user":
            return context.user_risk_score < 0.3
        
        # System load conditions
        elif condition == "high_load":
            return context.system_load > 0.8
        elif condition == "low_load":
            return context.system_load < 0.3
        
        return False
    
    def calculate_adjusted_threshold(self, threshold_type: ThresholdType, context: ThresholdContext) -> Tuple[float, List[ThresholdAdjustment]]:
        """
        Calculate adjusted threshold based on context.
        
        Args:
            threshold_type: Type of threshold to calculate
            context: Current context
            
        Returns:
            Tuple of (adjusted_threshold, applied_adjustments)
        """
        base_threshold = self.thresholds[threshold_type]
        adjusted_value = base_threshold.current_value
        applied_adjustments = []
        
        # Apply context-based adjustments
        for factor, rules in self.adjustment_rules.items():
            for rule in rules:
                if self._evaluate_context_condition(rule.condition, context):
                    adjusted_value += rule.adjustment * rule.confidence
                    applied_adjustments.append(rule)
        
        # Apply bounds
        adjusted_value = max(base_threshold.min_value, 
                           min(base_threshold.max_value, adjusted_value))
        
        return adjusted_value, applied_adjustments
    
    def make_threshold_decision(self, ai_score: float, context: ThresholdContext) -> ThresholdDecision:
        """
        Make a moderation decision using adaptive thresholds.
        
        Args:
            ai_score: AI model confidence score (0-1)
            context: Decision context
            
        Returns:
            Threshold decision
        """
        # Calculate adjusted thresholds
        rejection_threshold, rejection_adjustments = self.calculate_adjusted_threshold(
            ThresholdType.REJECTION, context
        )
        manual_threshold, manual_adjustments = self.calculate_adjusted_threshold(
            ThresholdType.MANUAL_REVIEW, context
        )
        
        # Make decision
        if ai_score >= rejection_threshold:
            decision = "R"
            threshold_used = rejection_threshold
            threshold_type = ThresholdType.REJECTION
            adjustments = rejection_adjustments
            confidence = min(1.0, (ai_score - rejection_threshold) / (1.0 - rejection_threshold))
            reasoning = f"AI score {ai_score:.3f} exceeds rejection threshold {rejection_threshold:.3f}"
            
        elif ai_score >= manual_threshold:
            decision = "M"
            threshold_used = manual_threshold
            threshold_type = ThresholdType.MANUAL_REVIEW
            adjustments = manual_adjustments
            confidence = min(1.0, (ai_score - manual_threshold) / (rejection_threshold - manual_threshold))
            reasoning = f"AI score {ai_score:.3f} requires manual review (threshold {manual_threshold:.3f})"
            
        else:
            decision = "A"
            threshold_used = manual_threshold
            threshold_type = ThresholdType.APPROVAL
            adjustments = manual_adjustments
            confidence = min(1.0, (manual_threshold - ai_score) / manual_threshold)
            reasoning = f"AI score {ai_score:.3f} below manual review threshold {manual_threshold:.3f}"
        
        # Add adjustment reasoning
        if adjustments:
            adjustment_reasons = [adj.reason for adj in adjustments]
            reasoning += f" (Adjustments: {'; '.join(adjustment_reasons)})"
        
        decision_result = ThresholdDecision(
            decision=decision,
            confidence=confidence,
            threshold_used=threshold_used,
            threshold_type=threshold_type,
            adjustments_applied=adjustments,
            context=context,
            reasoning=reasoning
        )
        
        # Record decision for learning
        self._record_decision(decision_result, ai_score)
        
        return decision_result
    
    def _record_decision(self, decision: ThresholdDecision, ai_score: float):
        """Record decision for historical analysis and learning."""
        record = {
            'timestamp': time.time(),
            'decision': decision.decision,
            'ai_score': ai_score,
            'threshold_used': decision.threshold_used,
            'threshold_type': decision.threshold_type.value,
            'adjustments_count': len(decision.adjustments_applied),
            'context': {
                'content_type': decision.context.content_type,
                'content_length': decision.context.content_length,
                'sentiment_score': decision.context.sentiment_score,
                'primary_topic': decision.context.primary_topic,
                'time_of_day': decision.context.time_of_day
            }
        }
        
        self.decision_history.append(record)
        self.performance_metrics['total_decisions'] += 1
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze threshold performance and suggest adjustments.
        
        Returns:
            Performance analysis results
        """
        if len(self.decision_history) < 10:
            return {"status": "insufficient_data", "decisions_count": len(self.decision_history)}
        
        # Analyze decision patterns
        decisions = [d['decision'] for d in self.decision_history]
        decision_counts = {
            'R': decisions.count('R'),
            'M': decisions.count('M'),
            'A': decisions.count('A')
        }
        
        # Analyze by content type
        content_type_analysis = defaultdict(lambda: {'R': 0, 'M': 0, 'A': 0})
        for record in self.decision_history:
            content_type = record['context']['content_type']
            decision = record['decision']
            content_type_analysis[content_type][decision] += 1
        
        # Analyze threshold effectiveness
        recent_decisions = list(self.decision_history)[-100:]  # Last 100 decisions
        avg_ai_scores = {
            'R': [],
            'M': [],
            'A': []
        }
        
        for record in recent_decisions:
            avg_ai_scores[record['decision']].append(record['ai_score'])
        
        # Calculate average scores for each decision type
        avg_scores = {}
        for decision_type, scores in avg_ai_scores.items():
            if scores:
                avg_scores[decision_type] = {
                    'mean': sum(scores) / len(scores),
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores)
                }
        
        return {
            'status': 'analysis_complete',
            'total_decisions': len(self.decision_history),
            'decision_distribution': decision_counts,
            'content_type_analysis': dict(content_type_analysis),
            'average_scores_by_decision': avg_scores,
            'current_thresholds': {
                'rejection': self.thresholds[ThresholdType.REJECTION].current_value,
                'manual_review': self.thresholds[ThresholdType.MANUAL_REVIEW].current_value
            }
        }
    
    def update_thresholds_from_feedback(self, feedback_data: List[Dict[str, Any]]):
        """
        Update thresholds based on feedback data.
        
        Args:
            feedback_data: List of feedback records with actual outcomes
        """
        if not feedback_data:
            return
        
        # Analyze feedback to identify threshold adjustment needs
        false_positives = 0
        false_negatives = 0
        
        for feedback in feedback_data:
            predicted = feedback.get('predicted_decision')
            actual = feedback.get('actual_decision')
            
            if predicted == 'R' and actual in ['A', 'M']:
                false_positives += 1
            elif predicted == 'A' and actual in ['R', 'M']:
                false_negatives += 1
        
        total_feedback = len(feedback_data)
        false_positive_rate = false_positives / total_feedback
        false_negative_rate = false_negatives / total_feedback
        
        # Adjust thresholds based on error rates
        if false_positive_rate > 0.1:  # Too many false positives
            # Lower rejection threshold
            current_rejection = self.thresholds[ThresholdType.REJECTION]
            adjustment = -0.05 * (false_positive_rate - 0.1)
            new_value = max(current_rejection.min_value, 
                          current_rejection.current_value + adjustment)
            current_rejection.current_value = new_value
            current_rejection.last_updated = time.time()
            
            self.logger.info(f"Lowered rejection threshold to {new_value:.3f} due to high false positive rate")
        
        if false_negative_rate > 0.1:  # Too many false negatives
            # Lower manual review threshold
            current_manual = self.thresholds[ThresholdType.MANUAL_REVIEW]
            adjustment = -0.05 * (false_negative_rate - 0.1)
            new_value = max(current_manual.min_value,
                          current_manual.current_value + adjustment)
            current_manual.current_value = new_value
            current_manual.last_updated = time.time()
            
            self.logger.info(f"Lowered manual review threshold to {new_value:.3f} due to high false negative rate")
        
        # Update performance metrics
        self.performance_metrics['false_positives'] += false_positives
        self.performance_metrics['false_negatives'] += false_negatives
        
        if self.performance_metrics['total_decisions'] > 0:
            total_errors = (self.performance_metrics['false_positives'] + 
                          self.performance_metrics['false_negatives'])
            self.performance_metrics['accuracy'] = 1.0 - (total_errors / self.performance_metrics['total_decisions'])
    
    def get_threshold_context_from_analysis(self, enhanced_analysis: Dict[str, Any]) -> ThresholdContext:
        """
        Create threshold context from enhanced analysis results.
        
        Args:
            enhanced_analysis: Results from enhanced analysis
            
        Returns:
            Threshold context
        """
        context = ThresholdContext()
        
        # Extract sentiment information
        if 'sentiment' in enhanced_analysis:
            sentiment_data = enhanced_analysis['sentiment']
            if isinstance(sentiment_data, dict):
                context.sentiment_score = sentiment_data.get('sentiment_score', 0.0)
                context.sentiment_label = sentiment_data.get('sentiment_label', 'neutral')
        
        # Extract topic information
        if 'topic' in enhanced_analysis:
            topic_data = enhanced_analysis['topic']
            if isinstance(topic_data, dict):
                context.primary_topic = topic_data.get('primary_topic', 'general')
                context.content_type = topic_data.get('content_type', 'general')
                context.language = topic_data.get('language', 'en')
        
        # Extract text analysis information
        if 'text_analysis' in enhanced_analysis:
            text_data = enhanced_analysis['text_analysis']
            if isinstance(text_data, dict):
                context.content_length = text_data.get('word_count', 0)
        
        # Set time of day
        import datetime
        context.time_of_day = datetime.datetime.now().hour
        
        # Set default system load (would be calculated from actual system metrics)
        context.system_load = 0.5
        
        # Set default user risk score (would come from user management system)
        context.user_risk_score = 0.5
        
        context.enhanced_analysis = enhanced_analysis
        
        return context


# Global threshold manager instance
_threshold_manager: Optional[DynamicThresholdManager] = None


def get_threshold_manager() -> DynamicThresholdManager:
    """Get global threshold manager instance."""
    global _threshold_manager
    if _threshold_manager is None:
        _threshold_manager = DynamicThresholdManager()
    return _threshold_manager


def make_adaptive_decision(ai_score: float, enhanced_analysis: Dict[str, Any]) -> ThresholdDecision:
    """
    Convenience function to make adaptive threshold decision.
    
    Args:
        ai_score: AI model confidence score
        enhanced_analysis: Enhanced analysis results
        
    Returns:
        Threshold decision
    """
    manager = get_threshold_manager()
    context = manager.get_threshold_context_from_analysis(enhanced_analysis)
    return manager.make_threshold_decision(ai_score, context)
