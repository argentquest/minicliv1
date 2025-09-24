"""
Unit tests for SettingsService.
Tests environment settings retrieval and updates.
"""

import pytest
from unittest.mock import Mock, patch
from web_backend.services.settings_service import SettingsService, settings_service
from common.env_manager import EnvManager
from security_utils import SecurityUtils
from web1.theme import theme_manager


@pytest.fixture
def mock_env_manager():
    mock = Mock(spec=EnvManager)
    mock.load_env_file.return_value = {
        "API_KEY": "sk-test",
        "DEFAULT_MODEL": "openai/gpt-3.5-turbo",
        "VALIDATE_SSL": "true"
    }
    mock.get_env_descriptions.return_value = {
        "API_KEY": "Your API key",
        "DEFAULT_MODEL": "Default model",
        "VALIDATE_SSL": "SSL validation (true/false)"
    }
    return mock


@pytest.fixture
def mock_theme_manager():
    mock = Mock()
    mock.current_theme_name = "light"
    mock.get_available_themes.return_value = ["light", "dark"]
    return mock


def test_get_settings(mock_env_manager, mock_theme_manager):
    """Test get_settings returns values, masked, descriptions, theme."""
    with patch('web_backend.services.settings_service.env_manager', mock_env_manager), \
         patch('web_backend.services.settings_service.theme_manager', mock_theme_manager):
        
        result = settings_service.get_settings()
        
        assert "values" in result
        assert result["values"]["API_KEY"] == "sk-test"
        assert "masked" in result
        assert result["masked"]["API_KEY"] == SecurityUtils.mask_api_key("sk-test")
        assert "descriptions" in result
        assert result["descriptions"]["VALIDATE_SSL"] == "SSL validation (true/false)"
        assert result["theme"] == "light"
        assert result["availableThemes"] == ["light", "dark"]


def test_update_env(mock_env_manager, mock_theme_manager):
    """Test update_env calls env_manager.update_single_var for each change."""
    changes = {"API_KEY": "new_key", "VALIDATE_SSL": "false"}
    mock_env_manager.update_single_var.return_value = True
    
    with patch('web_backend.services.settings_service.env_manager', mock_env_manager), \
         patch('web_backend.services.settings_service.theme_manager', mock_theme_manager):
        
        result = settings_service.update_env(changes)
        
        assert result == {"API_KEY": True, "VALIDATE_SSL": True}
        assert mock_env_manager.update_single_var.call_count == 2
        mock_env_manager.update_single_var.assert_any_call("API_KEY", "new_key")
        mock_env_manager.update_single_var.assert_any_call("VALIDATE_SSL", "false")