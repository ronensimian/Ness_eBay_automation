import json
import os
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class DataReader:
    """Enterprise-grade utility to read test data from external files."""
    
    @staticmethod
    def get_project_root() -> str:
        """Returns the absolute path to the project root."""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def read_json(file_name: str) -> Dict[str, Any]:
        """Reads a JSON file from the data directory with error handling."""
        file_path = os.path.join(DataReader.get_project_root(), "data", file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Successfully loaded test data from {file_name}")
                return data
        except FileNotFoundError:
            logger.error(f"Test data file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading {file_path}: {e}")
            raise
