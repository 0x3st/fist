import json
from typing import Dict, Any
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

class AIConnector:
    '''
    The class for the AI model.
    '''
    def __init__(self, api_key: str, base_url: str, ) -> None:
        '''
        The constructor for the AI model.

        Args:
            api_key(str): the api key for the AI model.
            base_url(str): the base url for the AI model.
        '''
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.system_prompt = """
        You are a content moderator. Analyze the provided text and return the probability that the content is inappropriate.
        Return ONLY a JSON object with these fields:
        - "inappropriate_probability": number (0-100) - percentage probability that content is inappropriate
        - "reason": brief explanation of your assessment

        Example outputs:
        {
            "inappropriate_probability": 5,
            "reason": "Content appears appropriate with minor concerns about language tone"
        }

        OR

        {
            "inappropriate_probability": 85,
            "reason": "Contains explicit violent content and hate speech"
        }
        """
        self.model = "deepseek-chat"

    def moderate_content(self, content: str) -> Dict[str, Any]:
        '''
        Moderate the provided content using the AI model.

        Args:
            content(str): The content to be moderated.

        Returns:
            dict: A dictionary containing moderation results with keys:
                - "inappropriate_probability": number (0-100) indicating probability content is inappropriate
                - "reason": brief explanation of assessment
        '''
        user_prompt = content

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={
                    'type': 'json_object'
                }
            )

            response_content = response.choices[0].message.content
            if response_content is not None:
                return json.loads(response_content)
            else:
                return {
                    "inappropriate_probability": 100,
                    "reason": "Empty response from AI model"
                }
        except Exception as e:
            return {
                "inappropriate_probability": 100,
                "reason": f"Error processing content: {str(e)}"
            }

    def set_model(self, model: str) -> None:
        '''
        Set the AI model to use for content moderation.

        Args:
            model(str): The model name to use.
        '''
        self.model = model

    def set_system_prompt(self, prompt: str) -> None:
        '''
        Set a custom system prompt for content moderation.

        Args:
            prompt(str): The system prompt to use.
        '''
        self.system_prompt = prompt
