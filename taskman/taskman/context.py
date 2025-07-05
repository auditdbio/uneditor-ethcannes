"""
Context management for taskman.
Handles call stack tracking, state management, and context variables.
"""
from contextvars import ContextVar
from typing import List, Optional, Any

# Global counters for indexing
global_counters: dict[str, int] = {}

# Context variables
call_stack_var: ContextVar[List[str]] = ContextVar("call_stack", default=[])
current_func_var: ContextVar[Optional[str]] = ContextVar("current_func", default=None)
current_index_var: ContextVar[str] = ContextVar("current_index", default="")
current_attempt_var: ContextVar[int] = ContextVar("current_attempt", default=0)

# For storing append_log function
append_log_var: ContextVar[Optional[Any]] = ContextVar("append_log", default=None)
append_log_is_async_var: ContextVar[bool] = ContextVar("append_log_is_async", default=False)


def get_next_index(parent_index: str) -> int:
    """Get the next available index for the parent context"""
    if parent_index not in global_counters:
        global_counters[parent_index] = 0
    next_index = global_counters[parent_index]
    global_counters[parent_index] += 1
    return next_index


def get_call_chain() -> List[str]:
    """Get the current call chain."""
    return call_stack_var.get().copy()


def get_current_index() -> str:
    """Get the current index."""
    return current_index_var.get()


def get_current_attempt() -> int:
    """Get the current attempt number."""
    return current_attempt_var.get()


def reset_global_counters() -> None:
    """Reset global counters for testing purposes."""
    global global_counters
    global_counters = {} 