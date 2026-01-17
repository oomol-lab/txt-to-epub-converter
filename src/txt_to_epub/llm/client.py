"""
LLM API client wrapper
"""
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API client wrapper - OpenAI compatible"""

    def __init__(self, api_key: str = None, model: str = "gpt-4-turbo",
                 base_url: str = None, organization: str = None):
        """
        Initialize LLM client

        :param api_key: OpenAI API key (if None, will read from environment variables)
        :param model: Model to use
        :param base_url: API base URL (for compatibility with other services)
        :param organization: OpenAI organization ID (optional)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Please run: pip install openai"
            )

        # Initialize OpenAI client
        client_kwargs = {}
        if api_key:
            client_kwargs['api_key'] = api_key
        if base_url:
            client_kwargs['base_url'] = base_url
        if organization:
            client_kwargs['organization'] = organization

        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.max_tokens = 128000

        # Statistics information
        self.stats = {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }

        # Model pricing (USD per 1K tokens)
        self.pricing = {
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
        }

        logger.info(f"LLM client initialized: model={model}")

    def call(self, prompt: str, max_tokens: int = None, temperature: float = 0.1) -> str:
        """
        Call LLM API

        :param prompt: Prompt text
        :param max_tokens: Maximum token count
        :param temperature: Temperature parameter (0-2, lower means more deterministic)
        :return: LLM response text
        """
        try:
            self.stats['total_calls'] += 1

            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a professional document structure analysis assistant, skilled at identifying chapters and table of contents structure. Please always return results in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Determine actual max_tokens to use
            actual_max_tokens = max_tokens or self.max_tokens

            # If max_tokens > 5000, must use stream=True
            use_streaming = actual_max_tokens > 5000

            if use_streaming:
                # Use streaming call
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=actual_max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    stream=True
                )

                # Collect streaming response
                content = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content

                # Note: streaming response has no usage info, use estimated values
                # Rough estimate: 1 token ≈ 4 characters for Chinese, 1.3 for English
                estimated_prompt_tokens = len(prompt) // 3
                estimated_completion_tokens = len(content) // 3

                self.stats['total_input_tokens'] += estimated_prompt_tokens
                self.stats['total_output_tokens'] += estimated_completion_tokens

                logger.debug(f"LLM streaming call successful: ~{estimated_prompt_tokens} in + ~{estimated_completion_tokens} out tokens (estimated)")

            else:
                # Use non-streaming call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=actual_max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )

                # Extract response text
                content = response.choices[0].message.content

                # Update statistics
                usage = response.usage
                self.stats['total_input_tokens'] += usage.prompt_tokens
                self.stats['total_output_tokens'] += usage.completion_tokens

                # Calculate cost
                model_key = self.model
                if model_key not in self.pricing:
                    # Try matching prefix
                    for key in self.pricing:
                        if self.model.startswith(key):
                            model_key = key
                            break

                if model_key in self.pricing:
                    pricing = self.pricing[model_key]
                    input_cost = usage.prompt_tokens * pricing['input'] / 1000
                    output_cost = usage.completion_tokens * pricing['output'] / 1000
                    self.stats['total_cost'] += input_cost + output_cost

                logger.debug(f"LLM call successful: {usage.prompt_tokens} in + {usage.completion_tokens} out tokens")

            return content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }
