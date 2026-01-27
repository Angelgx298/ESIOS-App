import logging
import sys
from esios_ingestor.core.config import settings

def setup_logging():
    """Configures the root logger to output JSON-like structure or simple text."""
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
