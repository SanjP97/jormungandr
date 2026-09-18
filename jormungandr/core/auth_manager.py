"""Authentication Manager"""

from typing import Dict, Any, Optional
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class AuthManager:
    """Manage authentication for API requests"""
    
    def __init__(self, auth_config: Dict[str, Any]):
        self.auth_type = auth_config.get("type", "none")
        self.credentials = auth_config.get("credentials", {})
        
        logger.info(f"{self.auth_type.capitalize()} authentication configured")
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        
        if self.auth_type == "bearer":
            token = self.credentials.get("token")
            if not token:
                logger.error("Bearer token not found in credentials")
                return {}
            
            return {
                "Authorization": f"Bearer {token}"
            }
        
        elif self.auth_type == "api_key":
            api_key = self.credentials.get("api_key")
            header_name = self.credentials.get("header_name", "X-API-Key")
            
            if not api_key:
                logger.error("API key not found in credentials")
                return {}
            
            return {
                header_name: api_key
            }
        
        elif self.auth_type == "basic":
            username = self.credentials.get("username")
            password = self.credentials.get("password")
            
            if not username or not password:
                logger.error("Username or password not found in credentials")
                return {}
            
            import base64
            credentials = f"{username}:{password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            return {
                "Authorization": f"Basic {encoded}"
            }
        
        elif self.auth_type == "none":
            return {}
        
        else:
            logger.warning(f"Unknown authentication type: {self.auth_type}")
            return {}
    
    def refresh_token(self) -> bool:
        """Refresh authentication token if supported"""
        
        if self.auth_type == "bearer":
            # Check if refresh is configured
            refresh_config = self.credentials.get("refresh", {})
            
            if not refresh_config.get("enabled", False):
                logger.warning("Token refresh not configured")
                return False
            
            # Implement token refresh logic here if needed
            logger.info("Token refresh not yet implemented")
            return False
        
        return False
