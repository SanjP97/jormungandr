"""JSON Export"""

import json
from pathlib import Path
from typing import Dict, Any, List
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class JSONExporter:
    """Export results to JSON"""
    
    def export(self, results: List[Dict[str, Any]], metrics: Dict[str, Any],
               metadata: Dict[str, Any], output_path: str):
        """Export to JSON"""
        output_data = {
            "run_metadata": metadata,
            "metrics": metrics,
            "category_scores": metrics["category_scores"],
            "overall_score": metrics["overall_score"],
            "guardrail_effectiveness": metrics.get("guardrail_effectiveness", {}),
            "samples": results
        }
        
        output_file = Path(output_path) / "results.json"
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"JSON export saved to: {output_file}")
        return str(output_file)
