"""Configuration Loader"""

import yaml
from pathlib import Path
from typing import Dict, Any
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """Load and validate configuration"""
    
    @staticmethod
    def load(config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from: {config_path}")
        return config
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """Validate configuration"""
        required_keys = ["app_name", "base_url", "auth", "endpoint", "dataset"]
        
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required configuration key: {key}")
                return False
        
        logger.info("Configuration validated successfully")
        return True
