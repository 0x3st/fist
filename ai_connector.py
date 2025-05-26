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
        You are a content moderator. Analyze the provided text and determine if it's appropriate.
        Return ONLY a JSON object with these fields:
        - "appropriate": boolean (true/false)
        - "confidence": number (1-10)
        - "reason": brief explanation (only if inappropriate)

        Example output:
        {
            "appropriate": true,
            "confidence": 9.2
        }

        OR

        {
            "appropriate": false,
            "confidence": 7.8,
            "reason": "Contains explicit violent content"
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
                - "appropriate": boolean indicating if content is appropriate
                - "confidence": number (1-10) indicating confidence level
                - "reason": brief explanation (only if inappropriate)
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
                    "appropriate": False,
                    "confidence": 1,
                    "reason": "Empty response from AI model"
                }
        except Exception as e:
            return {
                "appropriate": False,
                "confidence": 1,
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
