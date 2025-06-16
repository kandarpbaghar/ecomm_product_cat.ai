"""
LLM Provider Abstraction Layer
Supports OpenAI, Anthropic, and Google Gemini
"""

import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import json

# Import LLM libraries
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class LLMResponse:
    """Standardized response object across all providers"""
    def __init__(self, content: str, raw_response: Any = None):
        self.content = content
        self.raw_response = raw_response


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate chat completion from messages"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is properly configured and available"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT models provider"""
    
    def __init__(self, api_key: str):
        if not OpenAI:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4-turbo-preview", **kwargs) -> LLMResponse:
        """Generate chat completion using OpenAI"""
        try:
            # Ensure messages are in OpenAI format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            response = self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 500),
                stream=kwargs.get("stream", False)
            )
            
            if kwargs.get("stream", False):
                return response  # Return generator for streaming
            
            content = response.choices[0].message.content
            return LLMResponse(content=content, raw_response=response)
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(self.api_key and OpenAI)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude models provider"""
    
    def __init__(self, api_key: str):
        if not Anthropic:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        self.client = Anthropic(api_key=api_key)
        self.api_key = api_key
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "claude-3-sonnet-20240229", **kwargs) -> LLMResponse:
        """Generate chat completion using Anthropic"""
        try:
            # Convert messages to Anthropic format
            # Anthropic expects a system message separately
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    system_message = content
                elif role == "assistant":
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": content
                    })
                else:  # user
                    anthropic_messages.append({
                        "role": "user",
                        "content": content
                    })
            
            # Create the message
            create_params = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", 500),
                "temperature": kwargs.get("temperature", 0.7)
            }
            
            if system_message:
                create_params["system"] = system_message
            
            response = self.client.messages.create(**create_params)
            
            # Extract content from response
            content = response.content[0].text if response.content else ""
            return LLMResponse(content=content, raw_response=response)
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Anthropic is properly configured"""
        return bool(self.api_key and Anthropic)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini models provider"""
    
    def __init__(self, api_key: str):
        if not genai:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        genai.configure(api_key=api_key)
        self.api_key = api_key
        self.model = None
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = "gemini-pro", **kwargs) -> LLMResponse:
        """Generate chat completion using Gemini"""
        try:
            # Initialize model if needed
            if not self.model or self.model.model_name != f"models/{model}":
                self.model = genai.GenerativeModel(model)
            
            # Convert messages to Gemini format
            # Gemini uses a chat session approach
            chat = self.model.start_chat(history=[])
            
            # Process messages
            for msg in messages[:-1]:  # All but the last message as history
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    # Gemini doesn't have explicit system messages
                    # We'll prepend it to the first user message
                    continue
                elif role == "assistant":
                    # Add as model response in history
                    chat.history.append({
                        "role": "model",
                        "parts": [content]
                    })
                else:  # user
                    chat.history.append({
                        "role": "user",
                        "parts": [content]
                    })
            
            # Send the last message
            if messages:
                last_msg = messages[-1]
                
                # Handle system message if it's the only message
                if len(messages) == 1 and last_msg.get("role") == "system":
                    response = chat.send_message(last_msg.get("content", ""))
                else:
                    # Prepend system message if exists
                    system_content = next((m["content"] for m in messages if m.get("role") == "system"), "")
                    user_content = last_msg.get("content", "")
                    
                    if system_content and last_msg.get("role") == "user":
                        full_content = f"{system_content}\n\n{user_content}"
                    else:
                        full_content = user_content
                    
                    response = chat.send_message(full_content)
            
            return LLMResponse(content=response.text, raw_response=response)
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Gemini is properly configured"""
        return bool(self.api_key and genai)


class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GeminiProvider
    }
    
    MODELS = {
        "openai": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str) -> BaseLLMProvider:
        """Create an LLM provider instance"""
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(api_key)
    
    @classmethod
    def get_available_models(cls, provider_name: str) -> List[str]:
        """Get list of available models for a provider"""
        return cls.MODELS.get(provider_name, [])
    
    @classmethod
    def get_providers(cls) -> List[str]:
        """Get list of all supported providers"""
        return list(cls.PROVIDERS.keys())