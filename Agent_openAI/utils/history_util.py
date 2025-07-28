"""Message History with token tracking"""

from typing import Any, List, Dict, Optional, Tuple

from openai.types.chat.chat_completion_message import ChatCompletionMessage

from loguru import logger

import tiktoken

class MessageHistory:
    """Manages chat history with token tracking and context management"""
    
    def __init__(
        self,
        model: str,
        system: str,
        context_window_tokens: int,
        client: Any,
        #enable_caching: bool = True,
    ):
        # If we use azure openai, it would be deployment name, hence tiktoken should use get_encoding instead of encoding_for_model
        self.model = model
        self.system = system
        self.context_window_tokens = context_window_tokens
        self.client = client
        # OpenAI ChatCompletionMessage need to be in the History for Function Calling
        self.messages: List[Dict[str, Any]|ChatCompletionMessage] = []
        self.total_tokens = 0
        # self.enable_caching = enable_caching
        # We follow (Input, Output) token count
        self.message_tokens: List[Tuple[int, int]] = []
        
        try:
            # encoding = tiktoken.encoding_for_model(model)
            encoding = tiktoken.get_encoding("o200k_base")
            system_token = len(encoding.encode(system))
        except Exception as e:
            logger.error(f"Error getting system token count for {self.model}: {e}")
            system_token = len(self.system)/4
        
        self.total_tokens = system_token
        
    async def add_message(
        self,
        role: str,
        content: str | Dict[str, Any] | ChatCompletionMessage,
        usage: Any | None = None,
    ) -> None:
        """Add a message to the history and track token usage
        
        Only Update message_tokens, total_tokens when role is assistant
        Usage is important for counting the token counting
        """
        
        logger.info(f"{role}: add {content} to history")
        
        if content == ChatCompletionMessage:
            self.messages.append(content)
        else:
            self.messages.append({
                "role": role,
                "content": content,
            })
        
        if role == "assistant":
            total_input = usage.prompt_tokens
            output_tokens = usage.completion_tokens
        
            current_turn_input = total_input - self.total_tokens
            
            self.message_tokens.append((current_turn_input, output_tokens))
            self.total_tokens += current_turn_input + output_tokens
            
    def truncate(self) -> None:
        """Remove oldest messages when context window is exceeded"""
        if self.total_tokens <= self.context_window_tokens:
            return
        
        TRUNCATION_NOTICE_TOKENS = 7
        TRUNCATION_MESSAGE = {
            "role": "user",
            "content": "[Earlier history has been truncated.]"
        }
        
        def remove_messages():
            """Remove messages from the history
            
            To handle User, Assistant pair or combination of User Assistant pair followed by Function Call
            """
            add_user_input = False
            
            self.messages.pop(0)
            self.messages.pop(0)
            
            if self.messages[0]["role"] == "tool":
                while self.messages[0]["role"] == "tool":
                    self.messages.pop(0)
                add_user_input = True
                
            if add_user_input:
                self.messages.insert(0, {"role": "user", "content": ""})
                
            if self.message_tokens:
                input_tokens, output_tokens = self.message_tokens.pop(0)
                self.total_tokens -= input_tokens + output_tokens
        
        while(
            self.message_tokens
            and self.total_tokens > self.context_window_tokens
            and len(self.messages) > 2
        ):
            logger.info(f"Truncating history to {self.context_window_tokens} tokens")
            remove_messages()
        
        if self.messages and self.message_tokens:
            # To show truncation notice
            self.messages[0] = TRUNCATION_MESSAGE

            original_input_tokens, original_output_tokens = self.message_tokens[0]
            self.message_tokens[0] = (
                TRUNCATION_NOTICE_TOKENS,
                original_output_tokens
            )
            
            self.total_tokens += (
                TRUNCATION_NOTICE_TOKENS - original_input_tokens
            )

    def format_for_api(self) -> List[Dict[str, Any]|ChatCompletionMessage]:
        """Format the history for OpenAI API"""
        result = []
        
        for message in self.messages:
            if isinstance(message, ChatCompletionMessage):
                result.append(message)
            else:
                result.append({
                    "role": message["role"],
                    "content": message["content"]
                })
                
        # if self.enable_caching and self.messages:
        # """Perform certain caching operations"""
        
        return result