"""
AI Processing Module for Code Chat with AI

This module implements the AI processing functionality for the Code Chat
application using a provider pattern architecture for better separation
of concerns and extensibility.

Architecture Overview:
- AIProviderFactory: Factory class for creating provider instances
- AIProcessor: Main processor class that maintains backward compatibility
- BaseAIProvider: Abstract base class that all providers must extend
- Provider implementations: OpenRouterProvider, TachyonProvider, etc.

The provider pattern allows:
- Easy addition of new AI providers without modifying core logic
- Consistent interface across different AI services
- Provider-specific optimizations and configurations
- Secure API key management and validation
- Comprehensive error handling and debugging

Key Features:
- Multiple AI provider support (OpenAI, Anthropic, etc.)
- Asynchronous processing with callbacks
- Secure API key validation and masking
- Conversation history management
- Model selection and configuration
- Debug information with sensitive data protection

Usage:
    # Create processor with default provider
    processor = create_ai_processor(api_key="your_key")

    # Create processor with specific provider
    processor = create_ai_processor(api_key="your_key", provider="tachyon")

    # Process a question
    response = processor.process_question(
        question="Explain this code",
        conversation_history=[],
        codebase_content="...",
        model="gpt-4"
    )
"""
from typing import List, Dict, Any, Callable, Optional
from .base_ai import BaseAIProvider
from providers.openrouter_provider import OpenRouterProvider
from providers.tachyon_provider import TachyonProvider
from providers.custom_provider import CustomProvider


class AIProviderFactory:
    """Factory class for creating AI provider instances."""

    # Static mapping of provider names to classes (for fallback)
    _STATIC_PROVIDERS = {
        "openrouter": OpenRouterProvider,
        "tachyon": TachyonProvider,
        "custom": CustomProvider
    }

    @classmethod
    def _get_dynamic_providers(cls) -> Dict[str, type]:
        """Get providers dynamically from environment configuration."""
        import os

        # Get providers list from environment
        providers_env = os.getenv("PROVIDERS", "")
        if not providers_env.strip():
            # Fallback to static providers if not configured
            return cls._STATIC_PROVIDERS.copy()

        # Parse provider list
        provider_names = [p.strip() for p in providers_env.split(',') if p.strip()]

        # Build dynamic provider mapping
        dynamic_providers = {}

        for provider_name in provider_names:
            if provider_name in cls._STATIC_PROVIDERS:
                dynamic_providers[provider_name] = cls._STATIC_PROVIDERS[provider_name]
            else:
                # Try to dynamically import custom providers
                try:
                    # Import from providers package
                    module_name = f"providers.{provider_name}_provider"
                    class_name = f"{provider_name.title()}Provider"

                    import importlib
                    module = importlib.import_module(module_name)
                    provider_class = getattr(module, class_name)

                    # Verify it's a valid provider class
                    if (hasattr(provider_class, '__bases__') and
                        any('BaseAIProvider' in str(base) for base in provider_class.__bases__)):
                        dynamic_providers[provider_name] = provider_class
                    else:
                        print(f"Warning: {class_name} is not a valid AI provider class")

                except (ImportError, AttributeError) as e:
                    print(f"Warning: Could not load provider '{provider_name}': {e}")
                    print(f"Make sure {provider_name}_provider.py exists in providers/ directory")

        # If no valid providers found, fallback to static
        if not dynamic_providers:
            print("Warning: No valid providers found in PROVIDERS environment variable")
            return cls._STATIC_PROVIDERS.copy()

        return dynamic_providers

    @classmethod
    def _get_providers(cls) -> Dict[str, type]:
        """Get the current provider mapping (dynamic or static)."""
        return cls._get_dynamic_providers()
    
    @classmethod
    def create_provider(cls, provider_name: str, api_key: str = "") -> BaseAIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_name: Name of the provider ('openrouter', 'tachyon', 'custom')
            api_key: API key for the provider

        Returns:
            AI provider instance

        Raises:
            ValueError: If provider is not supported
        """
        providers = cls._get_providers()
        if provider_name not in providers:
            available = ", ".join(providers.keys())
            raise ValueError(f"Unsupported provider '{provider_name}'. Available: {available}")

        provider_class = providers[provider_name]
        return provider_class(api_key)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available AI providers."""
        return list(cls._get_providers().keys())
    
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

        # Add to static providers for future use
        cls._STATIC_PROVIDERS[name] = provider_class

        # Ensure dynamically configured providers pick up the new entry
        try:
            import os

            providers_env = os.getenv('PROVIDERS')
            if providers_env:
                provider_list = [p.strip() for p in providers_env.split(',') if p.strip()]
                if name not in provider_list:
                    provider_list.append(name)
                    os.environ['PROVIDERS'] = ','.join(provider_list)
        except Exception:
            # If environment updates fail, continue with static mapping fallback
            pass


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