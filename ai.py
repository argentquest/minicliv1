"""
AI processing utilities for the Code Chat application.
Refactored to use provider pattern for better separation of concerns.
"""
from typing import List, Dict, Any, Callable, Optional, Union
from base_ai import BaseAIProvider
from openrouter_provider import OpenRouterProvider
from tachyon_provider import TachyonProvider


class AIProviderFactory:
    """Factory class for creating AI provider instances."""
    
    PROVIDERS = {
        "openrouter": OpenRouterProvider,
        "tachyon": TachyonProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str = "") -> BaseAIProvider:
        """
        Create an AI provider instance.
        
        Args:
            provider_name: Name of the provider ('openrouter', 'tachyon')
            api_key: API key for the provider
            
        Returns:
            AI provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider_name not in cls.PROVIDERS:
            available = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(f"Unsupported provider '{provider_name}'. Available: {available}")
        
        provider_class = cls.PROVIDERS[provider_name]
        return provider_class(api_key)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available AI providers."""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a new AI provider.
        
        Args:
            name: Provider name
            provider_class: Provider class that extends BaseAIProvider
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError("Provider class must extend BaseAIProvider")
        
        cls.PROVIDERS[name] = provider_class


class AIProcessor:
    """
    Main AI processor that delegates to provider-specific implementations.
    This class maintains backward compatibility with the existing API.
    """
    
    def __init__(self, provider: BaseAIProvider):
        """
        Initialize AI processor with a provider instance.
        
        Args:
            provider: An instance of a class that extends BaseAIProvider
        """
        if not isinstance(provider, BaseAIProvider):
            raise ValueError("provider must be an instance of BaseAIProvider")
        self._provider = provider
        self.provider_name = provider.get_provider_name()
    
    @property
    def api_key(self) -> str:
        """Get the current API key."""
        return self._provider.api_key
    
    @property
    def provider(self) -> str:
        """Get the current provider name."""
        return self.provider_name
    
    def set_api_key(self, api_key: str):
        """Set the API key."""
        self._provider.set_api_key(api_key)
    
    def set_provider(self, provider: str):
        """
        Set the AI provider.
        
        Args:
            provider: Provider name
        """
        if provider != self.provider_name:
            # Create new provider instance with current API key
            api_key = self._provider.api_key
            self._provider = AIProviderFactory.create_provider(provider, api_key)
            self.provider_name = provider
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is set."""
        return self._provider.validate_api_key()
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        return AIProviderFactory.get_available_providers()
    
    def get_provider_info(self, provider: str = None) -> Dict[str, Any]:
        """
        Get information about a specific provider or current provider.
        
        Args:
            provider: Provider name (optional, defaults to current provider)
            
        Returns:
            Provider information dictionary
        """
        if provider is None or provider == self.provider_name:
            return self._provider.get_provider_info()
        else:
            # Create temporary instance to get info
            temp_provider = AIProviderFactory.create_provider(provider)
            return temp_provider.get_provider_info()
    
    def get_provider_debug_info(self) -> Dict[str, Any]:
        """Get detailed debug information for the current provider with sensitive data masked."""
        # Use secure debug info instead of raw provider info
        base_info = self._provider.get_secure_debug_info()
        
        # Add provider-specific debug info if available (also masked)
        if hasattr(self._provider, 'get_debug_info'):
            debug_info = self._provider.get_debug_info()
            # Ensure provider-specific debug info is also secure
            from security_utils import SecurityUtils
            secure_debug_info = SecurityUtils.safe_debug_info(debug_info)
            base_info.update(secure_debug_info)
        
        return base_info
    
    def create_system_message(self, codebase_content: str) -> Dict[str, str]:
        """
        Create system message with codebase content.
        
        Args:
            codebase_content: Combined content from all codebase files
            
        Returns:
            System message dictionary
        """
        return self._provider.create_system_message(codebase_content)
    
    def process_question(
        self,
        question: str,
        conversation_history: List[Dict[str, str]],
        codebase_content: str,
        model: str,
        update_callback: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """
        Process a question using AI API.
        
        Args:
            question: User's question
            conversation_history: Previous conversation messages (without system message)
            codebase_content: Combined codebase content (only used for first message)
            model: AI model to use
            update_callback: Callback for UI updates (response, status)
            
        Returns:
            AI response content
            
        Raises:
            Exception: If API call fails or API key is invalid
        """
        return self._provider.process_question(
            question, conversation_history, codebase_content, model, update_callback
        )
    
    def process_question_async(
        self,
        question: str,
        conversation_history: List[Dict[str, str]],
        codebase_content: str,
        model: str,
        success_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        ui_update_callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Process question asynchronously with callbacks.
        
        Args:
            question: User's question
            conversation_history: Previous conversation messages
            codebase_content: Combined codebase content
            model: AI model to use
            success_callback: Called with AI response on success
            error_callback: Called with error message on failure
            ui_update_callback: Called for UI updates (response, status)
        """
        return self._provider.process_question_async(
            question, conversation_history, codebase_content, model,
            success_callback, error_callback, ui_update_callback
        )


# Backward compatibility aliases (optional)
AIProviderConfig = None  # Removed - now internal to providers


def create_ai_processor(api_key: str = "", provider: str = "openrouter") -> AIProcessor:
    """
    Factory function to create an AI processor.
    
    Args:
        api_key: API key for the provider
        provider: Provider name
        
    Returns:
        AI processor instance
    """
    provider_instance = AIProviderFactory.create_provider(provider, api_key)
    return AIProcessor(provider_instance)