"""
Configuration module for MCP Pi-hole Server.
Loads and validates configuration from config.toml and environment variables.
"""
import os
from typing import List, Literal, Optional
from pathlib import Path

import toml
from pydantic import BaseModel, HttpUrl, SecretStr, field_validator
from dotenv import load_dotenv


class PiholeConfig(BaseModel):
    """Configuration for Pi-hole connection."""
    api_url: HttpUrl
    application_password: SecretStr


class MCPServerFeaturesConfig(BaseModel):
    """Configuration for MCP Server features."""
    enable_metrics: bool = True
    enable_api: bool = True
    enable_web_interface: bool = True


class MCPServerConfig(BaseModel):
    """Configuration for MCP Server."""
    host: str
    port: int
    features: MCPServerFeaturesConfig
    authorized_api_keys: List[SecretStr] = []


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: Optional[Path] = None


class RootConfig(BaseModel):
    """Root configuration model."""
    pihole: PiholeConfig
    mcp_server: MCPServerConfig
    logging: LoggingConfig


def load_config(config_path: str = "config.toml") -> RootConfig:
    """
    Load configuration from config.toml and environment variables.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Validated RootConfig object
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config is invalid
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if config file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load config from file
    try:
        config_data = toml.load(config_path)
    except Exception as e:
        raise ValueError(f"Failed to parse config file: {e}")
    
    # Override with environment variables if set
    # Pi-hole password
    if os.getenv("PIHOLE_PASSWORD"):
        if "pihole" not in config_data:
            config_data["pihole"] = {}
        config_data["pihole"]["application_password"] = os.getenv("PIHOLE_PASSWORD")
    
    # MCP API keys (comma-separated)
    if os.getenv("MCP_API_KEYS"):
        api_keys = [key.strip() for key in os.getenv("MCP_API_KEYS", "").split(",") if key.strip()]
        if "mcp_server" not in config_data:
            config_data["mcp_server"] = {}
        config_data["mcp_server"]["authorized_api_keys"] = api_keys
    
    # Validate and return the config
    try:
        return RootConfig.model_validate(config_data)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")
