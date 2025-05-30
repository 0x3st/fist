"""
Business logic services for FIST Content Moderation System.

This module contains the core business logic for content moderation,
including content piercing, AI integration, and decision analysis.
"""
import random
from typing import List, Optional, Dict, Any

from ai_connector import AIConnector
from config import Config


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

    def moderate_content(
        self,
        content: str,
        percentages: Optional[List[float]] = None,
        thresholds: Optional[List[int]] = None,
        probability_thresholds: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Perform complete content moderation."""
        words = content.split()
        if len(words) == 1 and len(content.strip()) > 10:
            words = list(content.strip())
        word_count = len(words)

        pierced_content, percentage_used = self.pierce_content(content, percentages, thresholds)
        ai_result = self.check_content_with_ai(pierced_content)
        analysis = self.analyze_result(ai_result, probability_thresholds)

        return {
            "original_content": content,
            "pierced_content": pierced_content,
            "word_count": word_count,
            "percentage_used": percentage_used,
            "ai_result": ai_result,
            "final_decision": analysis["final_decision"],
            "reason": analysis["reason"]
        }
