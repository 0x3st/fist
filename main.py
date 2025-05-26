'''
This is the main file for the FIST system.

The system contains:
- a web scraper(web-scraper) to scrape the content from the website.
- a AI model(ai-connecter) to check the content.
- a database to store the content and the result.
- a API connector to change the database.
- a webserver for admin page.
'''
# import modules
import random
from typing import Optional, Dict, Any
from text_class import readyText
from ai_connector import AIConnector

# global variables
g_percentages = [0.8,0.6,0.4,0.2]
g_thresholds = [500, 1000, 3000]
g_confidence_threshold = 7.0  # Minimum confidence level to trust AI decision

g_file_url = "test_content_3_appropriate_long.txt"
g_text = readyText(g_file_url)

g_api_key = "sk-488d88049a9440a591bb948fa8fea5ca"
g_base_url = "https://api.deepseek.com"
g_ai_connector = AIConnector(g_api_key, g_base_url)

def piercer(
    text: str,
    percentages: Optional[list[float]] = None,
    thresholds: Optional[list[int]] = None
) -> str:
    '''
    The read the certain content and pierce it into pieces according to the rules.
    The percentage used depends on the word count and corresponding thresholds:
    For example, with default thresholds [500, 1000, 3000] and percentages [0.8, 0.6, 0.4, 0.2]:
        - 80% if the content is shorter than 500 words.
        - 60% if the content is 500-1000 words.
        - 40% if the content is 1000-3000 words.
        - 20% if the content is longer than 3000 words.

    Args:
        text(str): the content to be read.
        percentages(list): the percents to read.
        thresholds(list): word count thresholds for each percentage bracket.
                                    Defaults to [500, 1000, 3000] if None.
    Returns:
        str: the pierced content.
    '''
    # Handle Chinese text by treating characters as units if no spaces found
    words = text.split()
    if len(words) == 1 and len(text.strip()) > 10:
        # Likely Chinese text without spaces, treat each character as a unit
        words = list(text.strip())

    word_count = len(words)

    # Use default percentages if none provided
    if percentages is None:
        percentages = g_percentages

    # Use default thresholds if none provided
    if thresholds is None:
        thresholds = g_thresholds

    # Determine the percentage to keep based on word count
    # Find which bracket the word count falls into
    percentage_index = 0
    for i, threshold in enumerate(thresholds):
        if word_count < threshold:
            break
        percentage_index = i + 1

    # Use the appropriate percentage (with bounds checking)
    if percentage_index < len(percentages):
        percentage = percentages[percentage_index]
    else:
        # If we have fewer percentages than thresholds, use the last one
        percentage = percentages[-1]

    # Calculate how many words to keep
    words_to_keep = int(word_count * percentage)

    # Randomly choose a starting point for the selection
    if word_count > words_to_keep:
        max_start_index = word_count - words_to_keep
        start_index = random.randint(0, max_start_index)
    else:
        start_index = 0

    # Return the pierced content (random portion of the text)
    selected_words = words[start_index:start_index + words_to_keep]

    # If we're dealing with Chinese characters (single character words), join without spaces
    if len(words) > 1 and all(len(word) == 1 for word in words[:10]):  # Check first 10 to determine if Chinese
        return ''.join(selected_words)
    else:
        return ' '.join(selected_words)

def ai_checker(text: str) -> Dict[str, Any]:
    '''
    The function to check the content with AI.

    Args:
        text(str): the content to be checked.

    Returns:
        dict: the result of the AI check.
    '''
    global g_ai_connector
    return g_ai_connector.moderate_content(text)

def result_judge(ai_result: Dict[str, Any], confidence_threshold: float = 7.0) -> Dict[str, Any]:
    '''
    Judge the final result based on AI moderation output.

    Args:
        ai_result(dict): The result from AI moderation containing:
            - "appropriate": boolean indicating if content is appropriate
            - "confidence": number (1-10) indicating confidence level
            - "reason": brief explanation (only if inappropriate)
        confidence_threshold(float): Minimum confidence level to trust the result (default: 7.0)

    Returns:
        dict: Final judgment containing:
            - "final_decision": string ("APPROVED", "REJECTED", "MANUAL_REVIEW")
            - "ai_appropriate": boolean from AI
            - "ai_confidence": number from AI
            - "reason": explanation for the decision
            - "requires_manual_review": boolean
    '''
    appropriate = ai_result.get("appropriate", False)
    confidence = ai_result.get("confidence", 0)
    ai_reason = ai_result.get("reason", "")

    # High confidence decisions
    if confidence >= confidence_threshold:
        if appropriate:
            return {
                "final_decision": "APPROVED",
                "ai_appropriate": appropriate,
                "ai_confidence": confidence,
                "reason": f"AI approved with high confidence ({confidence}/10)",
                "requires_manual_review": False
            }
        else:
            return {
                "final_decision": "REJECTED",
                "ai_appropriate": appropriate,
                "ai_confidence": confidence,
                "reason": f"AI rejected with high confidence ({confidence}/10): {ai_reason}",
                "requires_manual_review": False
            }

    # Low confidence decisions - require manual review
    else:
        decision_text = "approved" if appropriate else "rejected"
        return {
            "final_decision": "MANUAL_REVIEW",
            "ai_appropriate": appropriate,
            "ai_confidence": confidence,
            "reason": f"AI {decision_text} but with low confidence ({confidence}/10). Manual review required. {ai_reason}",
            "requires_manual_review": True
        }

def main() -> bool:
    '''
    The main function for the FIST system.

    Returns:
        bool: True if content is approved, False if rejected or requires manual review
    '''
    global g_text, g_percentages, g_thresholds, g_file_url, g_confidence_threshold

    # Pierce the content based on length
    original_content = g_text.content
    pierced_content = piercer(g_text.content)
    g_text.content = pierced_content

    # Get AI moderation result
    ai_result = ai_checker(g_text.content)

    # Judge the final result based on AI output
    final_judgment = result_judge(ai_result, g_confidence_threshold)

    # Print results for debugging/logging
    print("=== FIST Content Moderation Results ===")
    print(f"Original content length: {len(original_content.split())} words")
    print(f"Pierced content length: {len(pierced_content.split())} words")
    print(f"AI Result: {ai_result}")
    print(f"Final Judgment: {final_judgment}")
    print("=" * 40)

    # Return decision based on final judgment
    decision = final_judgment.get("final_decision", "MANUAL_REVIEW")

    if decision == "APPROVED":
        print("✅ Content APPROVED")
        return True
    elif decision == "REJECTED":
        print("❌ Content REJECTED")
        return False
    else:  # MANUAL_REVIEW
        print("⚠️  Content requires MANUAL REVIEW")
        return False

if __name__ == "__main__":
    main()