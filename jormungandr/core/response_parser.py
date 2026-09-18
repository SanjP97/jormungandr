"""Response Parser - Extracts data from API responses"""

from typing import Any, Dict, List, Optional
from jsonpath_ng import parse
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class ResponseParser:
    """Parse and extract data from API responses"""
    
    def __init__(self, response_config: Dict[str, Any]):
        self.config = response_config
        self.output_path = response_config.get("output_path", "")
        self.success_indicators = response_config.get("success_indicators", [])
        self.guardrail_patterns = response_config.get("guardrail_patterns", {})
    
    def extract_output(self, response_data: Any) -> Optional[str]:
        """Extract LLM output from response"""
        if isinstance(response_data, str):
            return response_data
        
        if not self.output_path:
            return str(response_data)
        
        try:
            # Handle dot notation (e.g., "data.response.content")
            if "." in self.output_path:
                result = response_data
                for key in self.output_path.split("."):
                    if "[" in key and "]" in key:
                        # Handle array indexing (e.g., "choices[0]")
                        base_key = key.split("[")[0]
                        index = int(key.split("[")[1].split("]")[0])
                        result = result[base_key][index]
                    else:
                        result = result[key]
                return str(result)
            
            # Direct key access
            return str(response_data.get(self.output_path, ""))
        
        except Exception as e:
            logger.error(f"Failed to extract output using path '{self.output_path}': {e}")
            return None
    
    def is_success(self, response_data: Any) -> bool:
        """Check if response indicates success"""
        if not self.success_indicators:
            return True
        
        for indicator in self.success_indicators:
            path = indicator.get("path")
            expected_value = indicator.get("value")
            
            try:
                actual_value = self._get_value_by_path(response_data, path)
                if actual_value != expected_value:
                    return False
            except Exception as e:
                logger.warning(f"Failed to check success indicator '{path}': {e}")
                return False
        
        return True
    
    def detect_guardrail_action(self, response_data: Any, output_text: str) -> str:
        """
        Detect guardrail action: blocked, refused, partial, complied
        """
        # Check blocked indicators
        blocked_indicators = self.guardrail_patterns.get("blocked_indicators", [])
        for indicator in blocked_indicators:
            path = indicator.get("path")
            expected_value = indicator.get("value")
            
            try:
                actual_value = self._get_value_by_path(response_data, path)
                if actual_value == expected_value:
                    return "blocked"
            except:
                pass
        
        # Check refusal keywords in output text
        if output_text:
            refusal_keywords = self.guardrail_patterns.get("refusal_keywords", [])
            output_lower = output_text.lower()
            
            for keyword in refusal_keywords:
                if keyword.lower() in output_lower:
                    return "refused"
            
            # Check partial compliance
            partial_keywords = self.guardrail_patterns.get("partial_compliance", [])
            for keyword in partial_keywords:
                if keyword.lower() in output_lower:
                    return "partial"
        
        # Default: complied (generated content)
        return "complied"
    
    def _get_value_by_path(self, data: Any, path: str) -> Any:
        """Get value from nested structure using path"""
        if "." in path:
            result = data
            for key in path.split("."):
                if "[" in key and "]" in key:
                    base_key = key.split("[")[0]
                    index = int(key.split("[")[1].split("]")[0])
                    result = result[base_key][index]
                else:
                    result = result[key]
            return result
        return data.get(path)
