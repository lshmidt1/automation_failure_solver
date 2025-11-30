"""Configuration management for the POC."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        load_dotenv()
        self.config_path = config_path
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Override with environment variables
        config['llm']['api_key'] = os.getenv('OPENAI_API_KEY', config['llm'].get('api_key'))
        config['llm']['model'] = os.getenv('LLM_MODEL', config['llm'].get('model', 'gpt-4'))
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self._config.get('llm', {})
    
    @property
    def execution(self) -> Dict[str, Any]:
        """Get execution configuration."""
        return self._config.get('execution', {})
