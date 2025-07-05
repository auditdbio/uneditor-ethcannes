"""
Caching functionality for taskman.
Handles cache reading, writing, and path management.
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Any, Optional
import asyncio

import dill

from .config import get_cache_base_path


class CacheMissError(Exception):
    """Exception raised when a cache entry is not found."""
    pass


def get_cache_path(function_name: str, key: str) -> Path:
    """Get cache path for the function with the given key"""
    cache_base_path = get_cache_base_path()
    if cache_base_path is None:
        raise ValueError("Cache base path not configured")
    return cache_base_path / f"{function_name}_{key}.dill"


def read_cache_sync(cache_path: Path, function_name: str) -> Any:
    """
    Synchronously read cache from disk.
    
    Args:
        cache_path: Path to cache file
        function_name: Name of the function for logging
        
    Returns:
        Cached data if available.
        
    Raises:
        CacheMissError: If the cache entry is not found.
    """
    cache_base_path = get_cache_base_path()
    if cache_base_path is None:
        logging.debug(f"Caching disabled, skipping cache read for {function_name}")
        raise CacheMissError("Caching is disabled")
        
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                data = dill.loads(f.read())
                logging.debug(f"Cache hit for {function_name} with id {cache_path.stem}")
                return data
        except (dill.UnpicklingError, EOFError, IOError) as e:
            logging.warning(f"Failed to read cache from {cache_path}: {e}")
            raise CacheMissError(f"Failed to read cache: {e}")
    
    logging.debug(f"Cache miss for {function_name} with id {cache_path.stem}")
    raise CacheMissError("Cache miss")


def write_cache_sync(cache_path: Path, result: Any, function_name: str) -> None:
    """
    Synchronously and atomically write cache to disk, ensuring data is flushed.
    
    Args:
        cache_path: Path to cache file
        result: Data to cache
        function_name: Name of the function for logging
    """
    cache_base_path = get_cache_base_path()
    if cache_base_path is None:
        logging.debug(f"Caching disabled, skipping cache write for {function_name}")
        return
    
    temp_path = None
    try:
        # Ensure directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a unique temporary file
        temp_path = Path(f"{str(cache_path)}.{uuid.uuid4().hex}.tmp")

        with open(temp_path, "wb") as f:
            f.write(dill.dumps(result))
            # Flush Python-level buffers
            f.flush()
            # Flush OS-level buffers to disk to ensure data is written before rename
            os.fsync(f.fileno())

        # Atomically rename the temporary file to the target file
        os.rename(temp_path, cache_path)

        logging.debug(f"Cached result for {function_name} with id {cache_path.stem}")

    except (TypeError, dill.PicklingError, IOError, OSError) as e:
        logging.warning(f"Failed to write cache to {cache_path}: {e}")
        # Clean up temporary file if it exists
        try:
            if temp_path and temp_path.exists():
                os.unlink(temp_path)
        except Exception as cleanup_exc:
            logging.error(f"Failed to cleanup temp cache file {temp_path}: {cleanup_exc}")


async def read_cache_async(cache_path: Path, function_name: str) -> Any:
    """
    Asynchronously read cache from disk by running the sync version in an executor.
    
    Args:
        cache_path: Path to cache file
        function_name: Name of the function for logging
        
    Returns:
        Cached data if available.
        
    Raises:
        CacheMissError: If the cache entry is not found.
    """
    cache_base_path = get_cache_base_path()
    if cache_base_path is None:
        logging.debug(f"Caching disabled, skipping cache read for {function_name}")
        raise CacheMissError("Caching is disabled")
        
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(
            None, 
            read_cache_sync, 
            cache_path, 
            function_name
        )
    except CacheMissError:
        # Re-raise the specific exception to be caught by the decorator
        raise


async def write_cache_async(cache_path: Path, result: Any, function_name: str) -> None:
    """
    Asynchronously write cache to disk by running the sync version in an executor.
    
    Args:
        cache_path: Path to cache file
        result: Data to cache
        function_name: Name of the function for logging
    """
    cache_base_path = get_cache_base_path()
    if cache_base_path is None:
        logging.debug(f"Caching disabled, skipping cache write for {function_name}")
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, 
        write_cache_sync, 
        cache_path, 
        result, 
        function_name
    ) 