"""
Logging functionality for taskman.
Handles log file creation and management for tasks.
"""
from pathlib import Path
from typing import Any, Callable, Optional

import aiofiles

from .config import get_log_base_path
from .context import (
    append_log_var, 
    append_log_is_async_var, 
    current_attempt_var
)


async def _append_log_async(content: str) -> None:
    """Async version of append_log"""
    current_append_log = append_log_var.get()
    if current_append_log and append_log_is_async_var.get():
        await current_append_log(content)
    elif current_append_log:
        current_append_log(content)


def append_log(content: str) -> Any:
    """
    Function to append log content that works in both sync and async contexts.
    Will automatically detect if it's being called with await and do the right thing.
    """
    current_append_log = append_log_var.get()
    if current_append_log:
        # If we're in an async context and the append_log is async, return awaitable
        if append_log_is_async_var.get():
            return _append_log_async(content)
        # Otherwise, just call it directly
        return current_append_log(content)
    return None


def create_async_log_function(file_index: str) -> Callable[[str], Any]:
    """
    Create an async logging function for a specific task invocation.
    
    Args:
        file_index: Index for the log file name
        
    Returns:
        Async logging function
    """
    async def invocation_append_log(content: str) -> None:
        # If logging is disabled, just return
        log_base_path = get_log_base_path()
        if log_base_path is None:
            return
        
        # Get current attempt number at execution time
        current_attempt = current_attempt_var.get()
        
        # Create log file path based on current state
        if current_attempt > 0:
            log_file = log_base_path / f"call_{file_index}_{current_attempt}.md"
        else:
            log_file = log_base_path / f"call_{file_index}.md"
        
        # Create parent directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file (append, not overwrite)
        async with aiofiles.open(log_file, 'a', encoding='utf-8') as f:
            await f.write(f"{content}\n")
    
    return invocation_append_log


def create_sync_log_function(file_index: str) -> Callable[[str], None]:
    """
    Create a sync logging function for a specific task invocation.
    
    Args:
        file_index: Index for the log file name
        
    Returns:
        Sync logging function
    """
    def invocation_append_log(content: str) -> None:
        # If logging is disabled, just return
        log_base_path = get_log_base_path()
        if log_base_path is None:
            return
        
        # Get current attempt number at execution time
        current_attempt = current_attempt_var.get()
        
        # Create log file path based on current state
        if current_attempt > 0:
            log_file = log_base_path / f"call_{file_index}_{current_attempt}.md"
        else:
            log_file = log_base_path / f"call_{file_index}.md"
        
        # Create parent directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file (append, not overwrite)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{content}\n")
    
    return invocation_append_log 