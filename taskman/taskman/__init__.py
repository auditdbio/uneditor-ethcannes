"""
Taskman - A task management and execution framework.

This module provides decorators and utilities for managing tasks with features like:
- Retry logic with configurable delays
- Caching based on function arguments  
- Semaphore-based concurrency control
- Context tracking and logging
- Support for both sync and async functions
"""

# Import configuration functions
from .config import configure_cache_path, configure_log_path

# Import decorators - main public API
from .decorators import flow, task

# Import context access functions for use within tasks
from .context import get_call_chain, get_current_index, get_current_attempt

# Import logging function for use within tasks
from .logging import append_log

# Import utility types for type hints
from .utils import RetryDelayType, SemaphoreType

__all__ = [
    # Configuration
    "configure_cache_path",
    "configure_log_path",
    
    # Main decorators
    "flow", 
    "task",
    
    # Context functions (available within decorated functions)
    "get_call_chain",
    "get_current_index", 
    "get_current_attempt",
    
    # Logging function (available within decorated functions)
    "append_log",
    
    # Type hints
    "RetryDelayType",
    "SemaphoreType",
]
