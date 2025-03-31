"""
Tests for the configuration module.
"""
import os
import tempfile
from unittest.mock import patch
import pytest
from pathlib import Path

import toml
from pydantic import ValidationError

from app.config import load_config, RootConfig


@pytest.fixture
def valid_config_file():
    """Create a temporary valid config file."""
    config_data = {
        "pihole": {
            "api_url": "http://localhost:80/admin/api.php",
            "application_password": "test_password"
        },
        "mcp_server": {
            "host": "0.0.0.0",
            "port": 8000,
            "features": {
                "enable_metrics": True,
                "enable_api": True,
                "enable_web_interface": True
            },
            "authorized_api_keys": ["test_key1", "test_key2"]
        },
        "logging": {
            "level": "INFO",
            "log_file": None
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".toml", delete=False) as temp:
        toml.dump(config_data, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def invalid_config_file():
    """Create a temporary invalid config file with missing required fields."""
    config_data = {
        "pihole": {
            # Missing application_password
            "api_url": "http://localhost:80/admin/api.php"
        },
        "mcp_server": {
            "host": "0.0.0.0",
            # Missing port
            "features": {
                "enable_metrics": True,
                "enable_api": True,
                "enable_web_interface": True
            }
        },
        "logging": {
            "level": "INFO"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".toml", delete=False) as temp:
        toml.dump(config_data, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def invalid_type_config_file():
    """Create a temporary invalid config file with incorrect data types."""
    config_data = {
        "pihole": {
            "api_url": "not-a-url",  # Invalid URL
            "application_password": "test_password"
        },
        "mcp_server": {
            "host": "0.0.0.0",
            "port": "8000",  # String instead of int
            "features": {
                "enable_metrics": "yes",  # String instead of bool
                "enable_api": True,
                "enable_web_interface": True
            },
            "authorized_api_keys": ["test_key1", "test_key2"]
        },
        "logging": {
            "level": "INVALID_LEVEL",  # Invalid log level
            "log_file": None
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".toml", delete=False) as temp:
        toml.dump(config_data, temp)
        temp_path = temp.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_load_valid_config(valid_config_file):
    """Test loading a valid configuration file."""
    config = load_config(valid_config_file)
    assert isinstance(config, RootConfig)
    assert config.pihole.api_url == "http://localhost:80/admin/api.php"
    assert config.pihole.application_password.get_secret_value() == "test_password"
    assert config.mcp_server.host == "0.0.0.0"
    assert config.mcp_server.port == 8000
    assert config.mcp_server.features.enable_metrics is True
    assert len(config.mcp_server.authorized_api_keys) == 2
    assert config.logging.level == "INFO"


def test_missing_required_fields(invalid_config_file):
    """Test validation error for missing required fields."""
    with pytest.raises(ValueError) as excinfo:
        load_config(invalid_config_file)
    assert "Configuration validation failed" in str(excinfo.value)


def test_invalid_data_types(invalid_type_config_file):
    """Test validation error for incorrect data types."""
    with pytest.raises(ValueError) as excinfo:
        load_config(invalid_type_config_file)
    assert "Configuration validation failed" in str(excinfo.value)


def test_file_not_found():
    """Test file not found error."""
    with pytest.raises(FileNotFoundError) as excinfo:
        load_config("nonexistent_config.toml")
    assert "Configuration file not found" in str(excinfo.value)


@patch.dict(os.environ, {"PIHOLE_PASSWORD": "env_password"})
def test_env_password_override(valid_config_file):
    """Test overriding password from environment variable."""
    config = load_config(valid_config_file)
    assert config.pihole.application_password.get_secret_value() == "env_password"


@patch.dict(os.environ, {"MCP_API_KEYS": "key1,key2,key3"})
def test_env_api_keys_override(valid_config_file):
    """Test overriding API keys from environment variable."""
    config = load_config(valid_config_file)
    assert len(config.mcp_server.authorized_api_keys) == 3
    assert config.mcp_server.authorized_api_keys[0].get_secret_value() == "key1"
    assert config.mcp_server.authorized_api_keys[1].get_secret_value() == "key2"
    assert config.mcp_server.authorized_api_keys[2].get_secret_value() == "key3"


@patch.dict(os.environ, {"MCP_API_KEYS": "key1, key2,  key3"})
def test_env_api_keys_whitespace_handling(valid_config_file):
    """Test handling of whitespace in comma-separated API keys."""
    config = load_config(valid_config_file)
    assert len(config.mcp_server.authorized_api_keys) == 3
    assert config.mcp_server.authorized_api_keys[0].get_secret_value() == "key1"
    assert config.mcp_server.authorized_api_keys[1].get_secret_value() == "key2"
    assert config.mcp_server.authorized_api_keys[2].get_secret_value() == "key3"
