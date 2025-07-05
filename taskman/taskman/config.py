"""
Configuration management for taskman.
Handles cache and log path configuration.
"""
import os
import logging
from pathlib import Path
from typing import Union, Optional

# Global module configuration
CACHE_BASE_PATH: Optional[Path] = None
LOG_BASE_PATH: Optional[Path] = None


def configure_cache_path(path: Union[str, Path]) -> None:
    """
    Configure the base path for cache files.

    Args:
        path: Path where cache files will be stored
    """
    global CACHE_BASE_PATH
    CACHE_BASE_PATH = Path(path)
    os.makedirs(CACHE_BASE_PATH, exist_ok=True)
    logging.info(f"Cache base path configured: {CACHE_BASE_PATH}")


def configure_log_path(path: Union[str, Path]) -> None:
    """
    Configure the base path for log files.

    Args:
        path: Path where log files will be stored
    """
    global LOG_BASE_PATH
    LOG_BASE_PATH = Path(path)
    os.makedirs(LOG_BASE_PATH, exist_ok=True)
    logging.info(f"Log base path configured: {LOG_BASE_PATH}")


def get_cache_base_path() -> Optional[Path]:
    """Get the configured cache base path."""
    return CACHE_BASE_PATH


def get_log_base_path() -> Optional[Path]:
    """Get the configured log base path."""
    return LOG_BASE_PATH 