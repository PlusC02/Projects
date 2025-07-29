"""History Utility for ReAct Agent with Token tracking"""

from typing import List, Dict, Any, Tuple
from loguru import logger
import tiktoken

class MessageHistory:
    """Manage Chat History with token tracking and context management"""

    def __init__(
        self,
        model: str,
        system: str,
        context_window_size: int
    ):
        self.model = model
        self.system = system
        self.context_window_size = context_window_size
        self.total_tokens = 0
        self.messages: List[Dict[str, Any]] = []
        self.message_tokens: List[Tuple[int, int]] = []

        # model = gpt-4o for example
        encoding = tiktoken.encoding_for_model(model)

        try:
            system_tokens = len(encoding.encode(system))
        except Exception:
            logger.warning(f"Failed to encode system prompt for {model}. Using approximate token count.")
            system_tokens = len(system)/4

        self.system_tokens = system_tokens
        self.encoding = encoding
        logger.info(f"Message History Initialized")
    
    async def add_message(self, role: str, content: str, usage: Any = None) -> None:
        """Add a message to the history"""
        # Depends on Model, we may need to rewrite partly for this part if using multimodal model

        logger.info(f"{role} Added Message: {content}")

        self.messages.append({"role": role, "content": content})

        # For token tracking
        if role == "assistant" and usage:
            total_input = usage.prompt_tokens
            output_tokens = usage.completion_tokens

            current_input_tokens = total_input - self.total_tokens
            self.message_token.append((current_input_tokens, output_tokens))
            self.total_tokens += current_input_tokens + output_tokens

    async def truncate(self) -> None:
        """Truncate the history to the context window size when exceed"""
        if self.total_tokens < self.context_window_size:
            return
        
        TRUNCATION_NOTICE_TOKEN = 7
        TRUNCATION_NOTICE_MESSAGE = "[Earlier history has been truncated]"
        
        def remove_message_pair():
            self.messages.pop(0)
            self.messages.pop(0)

            if self.message_tokens:
                input_tokens, output_tokens = self.message_tokens.pop(0)
                self.total_tokens -= input_tokens + output_tokens

        while (
            self.message_tokens and
            self.total_tokens > self.context_window_size and 
            len(self.messages) >= 2
        ):
            remove_message_pair()

            if self.messages and self.message_tokens:
                original_input_tokens, original_output_tokens = self.message_tokens[0]
                self.messages[0] = TRUNCATION_NOTICE_MESSAGE
                self.message_tokens[0] = (TRUNCATION_NOTICE_TOKEN, original_output_tokens)
                self.total_tokens += TRUNCATION_NOTICE_TOKEN - original_input_tokens

    def format_for_api(self) -> List[Dict[str, Any]]:
        """Format the history for API call"""
        result = [
            {"role": m["role"], "content": m["content"]} for m in self.messages
        ]

        result.insert(0, {"role": "system", "content": self.system})
        return result    