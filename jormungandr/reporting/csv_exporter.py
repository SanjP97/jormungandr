"""CSV Export"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """Export results to CSV"""
    
    def export(self, results: List[Dict[str, Any]], output_path: str):
        """Export to CSV"""
        df = pd.DataFrame(results)
        
        output_file = Path(output_path) / "details.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"CSV export saved to: {output_file}")
        return str(output_file)
