'''
This is the main file for the FIST system.

The system contains:
- a web scraper(web-scraper) to scrape the content from the website.
- a AI model(ai-connecter) to assess content inappropriateness probability.
- a database to store the content and the result.
- a API connector to change the database.
- a webserver for admin page.

Architecture:
- AI component returns only probability scores (0-100%) with brief reasons
- analyze_result() function handles final decision-making logic based on configurable thresholds
- Clear separation between AI assessment and business logic decisions
- Simplified risk levels: LOW (≤20%) → APPROVED, MEDIUM (21-80%) → MANUAL_REVIEW, VERY_HIGH (>80%) → REJECTED
'''
# import modules
import random
from typing import Optional, Dict, Any
from text_class import readyText
from ai_connector import AIConnector

# global variables
g_percentages = [0.8,0.6,0.4,0.2]
g_thresholds = [500, 1000, 3000]
g_probability_thresholds = {"low": 20, "high": 80}  # Thresholds for decision making

g_file_url = "test.txt"
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

def analyze_result(ai_result: Dict[str, Any], probability_thresholds: Optional[Dict[str, int]] = None) -> Dict[str, str]:
    '''
    Analyze the AI moderation result and make the final decision based on probability thresholds.

    Args:
        ai_result(dict): The result from AI moderation containing:
            - "inappropriate_probability": number (0-100) indicating probability content is inappropriate
            - "reason": brief explanation of assessment
        probability_thresholds(dict): Thresholds for decision making. Defaults to:
            {"low": 50, "mid": 70}

    Returns:
        dict: Final decision containing:
            - "final_decision": string ("A", "R", "M") for Approved, Rejected, Manual check
            - "reason": explanation for the final decision
    '''
    # Default probability thresholds
    if probability_thresholds is None:
        probability_thresholds = {"low": 50, "mid": 70}

    inappropriate_prob = ai_result.get("inappropriate_probability", 50)  # Default to uncertain
    ai_reason = ai_result.get("reason", "No reason provided")

    # Determine decision based on probability
    if inappropriate_prob <= probability_thresholds["low"]:
        final_decision = "A"
        reason = f"Low risk ({inappropriate_prob}%): {ai_reason}"
    elif inappropriate_prob <= probability_thresholds["mid"]:
        final_decision = "M"
        reason = f"Medium risk ({inappropriate_prob}%): {ai_reason}"
    else:
        final_decision = "R"
        reason = f"High risk ({inappropriate_prob}%): {ai_reason}"

    return {
        "final_decision": final_decision,
        "reason": reason
    }

def main() -> Dict[str, str]:
    '''
    The main function for the FIST system.

    Returns:
        dict: Analysis results in format {final_decision, reason}
              where final_decision is A/R/M for Approved/Rejected/Manual check
    '''
    global g_text, g_percentages, g_thresholds, g_file_url, g_probability_thresholds

    # Pierce the content based on length
    pierced_content = piercer(g_text.content)
    g_text.content = pierced_content

    # Get AI moderation result
    ai_result = ai_checker(g_text.content)

    # Analyze the result to make final decision
    analysis = analyze_result(ai_result, g_probability_thresholds)

    return analysis

if __name__ == "__main__":
    main()