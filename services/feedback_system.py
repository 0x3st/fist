"""
Real-time Learning and Feedback System for FIST Content Moderation System.

This module provides:
- Real-time feedback collection and processing
- Continuous learning from moderation decisions
- Performance monitoring and adjustment
- Feedback-driven model improvement
- Human-in-the-loop learning
"""
import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import queue

from config import Config


class FeedbackType(Enum):
    """Types of feedback."""
    HUMAN_REVIEW = "human_review"
    USER_REPORT = "user_report"
    AUTOMATED_CHECK = "automated_check"
    PERFORMANCE_METRIC = "performance_metric"
    SYSTEM_CORRECTION = "system_correction"


class FeedbackSource(Enum):
    """Sources of feedback."""
    MODERATOR = "moderator"
    END_USER = "end_user"
    ADMIN = "admin"
    SYSTEM = "system"
    API_CLIENT = "api_client"


class DecisionOutcome(Enum):
    """Actual outcomes of moderation decisions."""
    CORRECTLY_APPROVED = "correctly_approved"
    CORRECTLY_REJECTED = "correctly_rejected"
    CORRECTLY_FLAGGED = "correctly_flagged"
    FALSE_POSITIVE = "false_positive"  # Incorrectly rejected/flagged
    FALSE_NEGATIVE = "false_negative"  # Incorrectly approved
    OVERTURNED = "overturned"  # Decision changed on appeal
    SYSTEM_CORRECTION = "system_correction"  # Automated system correction


@dataclass
class FeedbackRecord:
    """Individual feedback record."""
    feedback_id: str
    content_id: str
    original_content: str
    original_decision: str  # R, M, A
    actual_outcome: DecisionOutcome
    feedback_type: FeedbackType
    feedback_source: FeedbackSource
    confidence: float
    timestamp: float
    processing_time: float
    ai_score: float
    human_score: Optional[float]
    context: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class LearningUpdate:
    """Learning update based on feedback."""
    update_id: str
    affected_models: List[str]
    update_type: str  # threshold_adjustment, model_retrain, feature_weight
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    confidence: float
    feedback_count: int
    timestamp: float
    performance_impact: Dict[str, float]


@dataclass
class PerformanceSnapshot:
    """Performance metrics snapshot."""
    timestamp: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    average_confidence: float
    processing_time: float
    total_decisions: int
    feedback_count: int


class RealTimeLearningEngine:
    """Real-time learning engine that processes feedback continuously."""

    def __init__(self):
        """Initialize learning engine."""
        self.logger = logging.getLogger(__name__)

        # Feedback storage
        self.feedback_queue = queue.Queue()
        self.feedback_history = deque(maxlen=10000)  # Last 10k feedback records
        self.learning_updates = deque(maxlen=1000)   # Last 1k learning updates

        # Performance tracking
        self.performance_history = deque(maxlen=1000)
        self.current_metrics = {}

        # Learning parameters
        self.learning_rate = 0.01
        self.min_feedback_for_update = 10
        self.update_frequency = 300  # 5 minutes
        self.confidence_threshold = 0.7

        # Pattern detection
        self.error_patterns = defaultdict(list)
        self.improvement_opportunities = []

        # Threading for real-time processing
        self.processing_thread = None
        self.stop_processing = threading.Event()

        # Start processing
        self.start_processing()

        self.logger.info("Real-time learning engine initialized")

    def start_processing(self):
        """Start background processing thread."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.stop_processing.clear()
            self.processing_thread = threading.Thread(target=self._process_feedback_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            self.logger.info("Started feedback processing thread")

    def stop_processing_thread(self):
        """Stop background processing thread."""
        self.stop_processing.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        self.logger.info("Stopped feedback processing thread")

    def add_feedback(self, feedback: FeedbackRecord):
        """Add feedback to processing queue."""
        self.feedback_queue.put(feedback)
        self.logger.debug(f"Added feedback {feedback.feedback_id} to queue")

    def _process_feedback_loop(self):
        """Main feedback processing loop."""
        last_update_time = time.time()

        while not self.stop_processing.is_set():
            try:
                # Process queued feedback
                processed_count = 0
                while not self.feedback_queue.empty() and processed_count < 100:
                    try:
                        feedback = self.feedback_queue.get_nowait()
                        self._process_single_feedback(feedback)
                        processed_count += 1
                    except queue.Empty:
                        break

                # Periodic learning updates
                current_time = time.time()
                if current_time - last_update_time >= self.update_frequency:
                    self._perform_learning_update()
                    last_update_time = current_time

                # Sleep briefly to prevent busy waiting
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in feedback processing loop: {e}")
                time.sleep(5)  # Wait longer on error

    def _process_single_feedback(self, feedback: FeedbackRecord):
        """Process a single feedback record."""
        # Add to history
        self.feedback_history.append(feedback)

        # Analyze feedback for patterns
        self._analyze_feedback_patterns(feedback)

        # Update real-time metrics
        self._update_metrics(feedback)

        # Check for immediate learning opportunities
        self._check_immediate_learning(feedback)

        self.logger.debug(f"Processed feedback {feedback.feedback_id}")

    def _analyze_feedback_patterns(self, feedback: FeedbackRecord):
        """Analyze feedback for error patterns."""
        # Identify error patterns
        if feedback.actual_outcome in [DecisionOutcome.FALSE_POSITIVE, DecisionOutcome.FALSE_NEGATIVE]:
            error_key = f"{feedback.actual_outcome.value}_{feedback.original_decision}"
            self.error_patterns[error_key].append({
                'feedback': feedback,
                'timestamp': time.time()
            })

            # Keep only recent patterns (last 24 hours)
            cutoff_time = time.time() - 86400
            self.error_patterns[error_key] = [
                p for p in self.error_patterns[error_key]
                if p['timestamp'] > cutoff_time
            ]

    def _update_metrics(self, feedback: FeedbackRecord):
        """Update real-time performance metrics."""
        # Get recent feedback for metrics calculation
        recent_feedback = [
            f for f in self.feedback_history
            if time.time() - f.timestamp < 3600  # Last hour
        ]

        if len(recent_feedback) < 5:
            return

        # Calculate metrics
        total_decisions = len(recent_feedback)
        correct_decisions = sum(
            1 for f in recent_feedback
            if f.actual_outcome in [
                DecisionOutcome.CORRECTLY_APPROVED,
                DecisionOutcome.CORRECTLY_REJECTED,
                DecisionOutcome.CORRECTLY_FLAGGED
            ]
        )

        false_positives = sum(
            1 for f in recent_feedback
            if f.actual_outcome == DecisionOutcome.FALSE_POSITIVE
        )

        false_negatives = sum(
            1 for f in recent_feedback
            if f.actual_outcome == DecisionOutcome.FALSE_NEGATIVE
        )

        # Calculate rates
        accuracy = correct_decisions / total_decisions if total_decisions > 0 else 0
        false_positive_rate = false_positives / total_decisions if total_decisions > 0 else 0
        false_negative_rate = false_negatives / total_decisions if total_decisions > 0 else 0

        # Calculate precision and recall
        true_positives = sum(
            1 for f in recent_feedback
            if f.actual_outcome == DecisionOutcome.CORRECTLY_REJECTED and f.original_decision == 'R'
        )

        predicted_positives = sum(
            1 for f in recent_feedback
            if f.original_decision == 'R'
        )

        actual_positives = true_positives + false_negatives

        precision = true_positives / predicted_positives if predicted_positives > 0 else 0
        recall = true_positives / actual_positives if actual_positives > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Average confidence and processing time
        avg_confidence = sum(f.confidence for f in recent_feedback) / total_decisions
        avg_processing_time = sum(f.processing_time for f in recent_feedback) / total_decisions

        # Create performance snapshot
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            false_positive_rate=false_positive_rate,
            false_negative_rate=false_negative_rate,
            average_confidence=avg_confidence,
            processing_time=avg_processing_time,
            total_decisions=total_decisions,
            feedback_count=len(recent_feedback)
        )

        self.performance_history.append(snapshot)
        self.current_metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'average_confidence': avg_confidence,
            'processing_time': avg_processing_time
        }

    def _check_immediate_learning(self, feedback: FeedbackRecord):
        """Check if immediate learning update is needed."""
        # Check for critical errors that need immediate attention
        if feedback.actual_outcome in [DecisionOutcome.FALSE_POSITIVE, DecisionOutcome.FALSE_NEGATIVE]:
            if feedback.confidence > 0.9:  # High confidence error
                self.improvement_opportunities.append({
                    'type': 'high_confidence_error',
                    'feedback': feedback,
                    'priority': 'high',
                    'timestamp': time.time()
                })

        # Check for consistent error patterns
        error_key = f"{feedback.actual_outcome.value}_{feedback.original_decision}"
        recent_errors = [
            p for p in self.error_patterns[error_key]
            if time.time() - p['timestamp'] < 1800  # Last 30 minutes
        ]

        if len(recent_errors) >= 5:  # 5 similar errors in 30 minutes
            self.improvement_opportunities.append({
                'type': 'pattern_error',
                'pattern': error_key,
                'count': len(recent_errors),
                'priority': 'medium',
                'timestamp': time.time()
            })

    def _perform_learning_update(self):
        """Perform periodic learning updates."""
        if len(self.feedback_history) < self.min_feedback_for_update:
            return

        # Analyze recent feedback for learning opportunities
        recent_feedback = [
            f for f in self.feedback_history
            if time.time() - f.timestamp < self.update_frequency * 2
        ]

        if not recent_feedback:
            return

        # Calculate performance changes
        self._analyze_performance_trends()

        # Generate learning updates
        updates = self._generate_learning_updates(recent_feedback)

        for update in updates:
            self.learning_updates.append(update)
            self.logger.info(f"Generated learning update: {update.update_type}")

    def _analyze_performance_trends(self):
        """Analyze performance trends over time."""
        if len(self.performance_history) < 2:
            return

        recent_snapshots = list(self.performance_history)[-10:]  # Last 10 snapshots

        # Calculate trends
        accuracy_trend = self._calculate_trend([s.accuracy for s in recent_snapshots])
        precision_trend = self._calculate_trend([s.precision for s in recent_snapshots])
        recall_trend = self._calculate_trend([s.recall for s in recent_snapshots])

        # Log significant trends
        if accuracy_trend < -0.05:  # Accuracy dropping
            self.logger.warning(f"Accuracy trend declining: {accuracy_trend:.3f}")

        if precision_trend < -0.05:  # Precision dropping
            self.logger.warning(f"Precision trend declining: {precision_trend:.3f}")

        if recall_trend < -0.05:  # Recall dropping
            self.logger.warning(f"Recall trend declining: {recall_trend:.3f}")

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (slope) of values."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        # Linear regression slope
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope

    def _generate_learning_updates(self, feedback_list: List[FeedbackRecord]) -> List[LearningUpdate]:
        """Generate learning updates based on feedback."""
        updates = []

        # Threshold adjustment updates
        threshold_update = self._generate_threshold_update(feedback_list)
        if threshold_update:
            updates.append(threshold_update)

        # Feature weight updates
        feature_update = self._generate_feature_update(feedback_list)
        if feature_update:
            updates.append(feature_update)

        return updates

    def _generate_threshold_update(self, feedback_list: List[FeedbackRecord]) -> Optional[LearningUpdate]:
        """Generate threshold adjustment update."""
        false_positives = [f for f in feedback_list if f.actual_outcome == DecisionOutcome.FALSE_POSITIVE]
        false_negatives = [f for f in feedback_list if f.actual_outcome == DecisionOutcome.FALSE_NEGATIVE]

        if len(false_positives) > len(false_negatives) * 2:
            # Too many false positives, increase thresholds
            adjustment = 0.05
            return LearningUpdate(
                update_id=f"threshold_up_{int(time.time())}",
                affected_models=["threshold_manager"],
                update_type="threshold_adjustment",
                old_values={"adjustment": 0.0},
                new_values={"adjustment": adjustment},
                confidence=0.7,
                feedback_count=len(false_positives),
                timestamp=time.time(),
                performance_impact={"false_positive_reduction": 0.1}
            )

        elif len(false_negatives) > len(false_positives) * 2:
            # Too many false negatives, decrease thresholds
            adjustment = -0.05
            return LearningUpdate(
                update_id=f"threshold_down_{int(time.time())}",
                affected_models=["threshold_manager"],
                update_type="threshold_adjustment",
                old_values={"adjustment": 0.0},
                new_values={"adjustment": adjustment},
                confidence=0.7,
                feedback_count=len(false_negatives),
                timestamp=time.time(),
                performance_impact={"false_negative_reduction": 0.1}
            )

        return None

    def _generate_feature_update(self, feedback_list: List[FeedbackRecord]) -> Optional[LearningUpdate]:
        """Generate feature weight update."""
        # Analyze which features are associated with errors
        error_feedback = [
            f for f in feedback_list
            if f.actual_outcome in [DecisionOutcome.FALSE_POSITIVE, DecisionOutcome.FALSE_NEGATIVE]
        ]

        if len(error_feedback) < 5:
            return None

        # This is a simplified feature analysis
        # In practice, this would involve more sophisticated analysis
        return LearningUpdate(
            update_id=f"feature_weight_{int(time.time())}",
            affected_models=["ml_models"],
            update_type="feature_weight",
            old_values={"feature_weights": "current"},
            new_values={"feature_weights": "adjusted"},
            confidence=0.6,
            feedback_count=len(error_feedback),
            timestamp=time.time(),
            performance_impact={"accuracy_improvement": 0.02}
        )

    def get_current_performance(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.current_metrics.copy()

    def get_performance_history(self, hours: int = 24) -> List[PerformanceSnapshot]:
        """Get performance history for specified hours."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            snapshot for snapshot in self.performance_history
            if snapshot.timestamp > cutoff_time
        ]

    def get_learning_updates(self, hours: int = 24) -> List[LearningUpdate]:
        """Get learning updates for specified hours."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            update for update in self.learning_updates
            if update.timestamp > cutoff_time
        ]

    def get_error_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get current error patterns."""
        return dict(self.error_patterns)

    def get_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """Get current improvement opportunities."""
        # Return recent opportunities
        cutoff_time = time.time() - 3600  # Last hour
        return [
            opp for opp in self.improvement_opportunities
            if opp['timestamp'] > cutoff_time
        ]


class FeedbackCollector:
    """Collects feedback from various sources."""

    def __init__(self, learning_engine: RealTimeLearningEngine):
        """Initialize feedback collector."""
        self.learning_engine = learning_engine
        self.logger = logging.getLogger(__name__)

    def collect_human_review_feedback(
        self,
        content_id: str,
        original_content: str,
        original_decision: str,
        human_decision: str,
        human_confidence: float,
        reviewer_id: str,
        ai_score: float,
        processing_time: float,
        notes: str = ""
    ):
        """Collect feedback from human review."""
        # Determine actual outcome
        if original_decision == human_decision:
            if human_decision == 'R':
                outcome = DecisionOutcome.CORRECTLY_REJECTED
            elif human_decision == 'A':
                outcome = DecisionOutcome.CORRECTLY_APPROVED
            else:
                outcome = DecisionOutcome.CORRECTLY_FLAGGED
        else:
            if original_decision in ['R', 'M'] and human_decision == 'A':
                outcome = DecisionOutcome.FALSE_POSITIVE
            elif original_decision == 'A' and human_decision in ['R', 'M']:
                outcome = DecisionOutcome.FALSE_NEGATIVE
            else:
                outcome = DecisionOutcome.OVERTURNED

        feedback = FeedbackRecord(
            feedback_id=f"human_{content_id}_{int(time.time())}",
            content_id=content_id,
            original_content=original_content,
            original_decision=original_decision,
            actual_outcome=outcome,
            feedback_type=FeedbackType.HUMAN_REVIEW,
            feedback_source=FeedbackSource.MODERATOR,
            confidence=human_confidence,
            timestamp=time.time(),
            processing_time=processing_time,
            ai_score=ai_score,
            human_score=1.0 if human_decision == 'R' else 0.0,
            context={'reviewer_id': reviewer_id, 'human_decision': human_decision},
            notes=notes
        )

        self.learning_engine.add_feedback(feedback)
        self.logger.info(f"Collected human review feedback for content {content_id}")

    def collect_user_report_feedback(
        self,
        content_id: str,
        original_content: str,
        original_decision: str,
        user_complaint: str,
        ai_score: float,
        processing_time: float
    ):
        """Collect feedback from user reports."""
        # User reports typically indicate false negatives (content should have been rejected)
        outcome = DecisionOutcome.FALSE_NEGATIVE if original_decision == 'A' else DecisionOutcome.CORRECTLY_REJECTED

        feedback = FeedbackRecord(
            feedback_id=f"user_report_{content_id}_{int(time.time())}",
            content_id=content_id,
            original_content=original_content,
            original_decision=original_decision,
            actual_outcome=outcome,
            feedback_type=FeedbackType.USER_REPORT,
            feedback_source=FeedbackSource.END_USER,
            confidence=0.7,  # User reports have moderate confidence
            timestamp=time.time(),
            processing_time=processing_time,
            ai_score=ai_score,
            human_score=None,
            context={'complaint': user_complaint},
            notes=f"User complaint: {user_complaint}"
        )

        self.learning_engine.add_feedback(feedback)
        self.logger.info(f"Collected user report feedback for content {content_id}")

    def collect_system_correction_feedback(
        self,
        content_id: str,
        original_content: str,
        original_decision: str,
        corrected_decision: str,
        correction_reason: str,
        ai_score: float,
        processing_time: float
    ):
        """Collect feedback from automated system corrections."""
        # Determine outcome based on correction
        if original_decision != corrected_decision:
            if original_decision in ['R', 'M'] and corrected_decision == 'A':
                outcome = DecisionOutcome.FALSE_POSITIVE
            elif original_decision == 'A' and corrected_decision in ['R', 'M']:
                outcome = DecisionOutcome.FALSE_NEGATIVE
            else:
                outcome = DecisionOutcome.SYSTEM_CORRECTION
        else:
            outcome = DecisionOutcome.CORRECTLY_APPROVED  # No correction needed

        feedback = FeedbackRecord(
            feedback_id=f"system_{content_id}_{int(time.time())}",
            content_id=content_id,
            original_content=original_content,
            original_decision=original_decision,
            actual_outcome=outcome,
            feedback_type=FeedbackType.SYSTEM_CORRECTION,
            feedback_source=FeedbackSource.SYSTEM,
            confidence=0.8,
            timestamp=time.time(),
            processing_time=processing_time,
            ai_score=ai_score,
            human_score=None,
            context={'corrected_decision': corrected_decision, 'reason': correction_reason},
            notes=f"System correction: {correction_reason}"
        )

        self.learning_engine.add_feedback(feedback)
        self.logger.info(f"Collected system correction feedback for content {content_id}")


# Global instances
_learning_engine: Optional[RealTimeLearningEngine] = None
_feedback_collector: Optional[FeedbackCollector] = None


def get_learning_engine() -> RealTimeLearningEngine:
    """Get global learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = RealTimeLearningEngine()
    return _learning_engine


def get_feedback_collector() -> FeedbackCollector:
    """Get global feedback collector instance."""
    global _feedback_collector
    if _feedback_collector is None:
        learning_engine = get_learning_engine()
        _feedback_collector = FeedbackCollector(learning_engine)
    return _feedback_collector


def collect_human_feedback(
    content_id: str,
    original_content: str,
    original_decision: str,
    human_decision: str,
    human_confidence: float,
    reviewer_id: str,
    ai_score: float,
    processing_time: float,
    notes: str = ""
):
    """Convenience function to collect human feedback."""
    collector = get_feedback_collector()
    collector.collect_human_review_feedback(
        content_id, original_content, original_decision, human_decision,
        human_confidence, reviewer_id, ai_score, processing_time, notes
    )
