"""
logger.py - Centralized logging configuration
"""
import logging
import sys
from pathlib import Path

# Create logs directory
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Create a logger with both file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(LOG_DIR / f"{name}.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
