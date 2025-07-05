"""
Decorators module for taskman.
Contains the main @flow and @task decorators with retry, caching, and semaphore functionality.
"""
import asyncio
import functools
import inspect
import logging
import time
import types
import threading
import copy
from typing import Any, Callable, Optional, Tuple

_active_tasks_count = 0
_active_tasks_lock = threading.Lock()
_active_task_pictos: list[str] = []

from .cache import (
    CacheMissError,
    get_cache_path, 
    read_cache_async, 
    read_cache_sync, 
    write_cache_async, 
    write_cache_sync
)
from .config import get_cache_base_path, get_log_base_path
from .context import (
    append_log_is_async_var,
    append_log_var,
    call_stack_var,
    current_attempt_var,
    current_func_var,
    current_index_var,
    get_next_index,
)
from .logging import append_log, create_async_log_function, create_sync_log_function
from .utils import RetryDelayType, SemaphoreType, calculate_retry_delay, hash_json, hash_to_pictogram


def create_wrapper(func: Callable, func_type: str) -> Callable:
    """Common function to create wrapper for flow and task decorators"""
    is_async = inspect.iscoroutinefunction(func)
    
    async def async_wrapper(*args, **kwargs):
        # Save current context
        prev_stack = call_stack_var.get().copy()
        prev_func = current_func_var.get()
        prev_index = current_index_var.get()
        prev_attempt = current_attempt_var.get()
        prev_append_log = append_log_var.get()
        prev_append_log_is_async = append_log_is_async_var.get()
        
        # Generate new index
        if func_type == "flow" and not prev_func:  # First flow
            new_index = ""
        else:
            # Get next index for parent
            next_idx = get_next_index(prev_index)
            
            if func_type == "flow":
                new_index = f"{prev_index}_{next_idx}"
            else:  # task
                new_index = f"{prev_index}_{next_idx}_{func.__name__}"
        
        # Update context
        current_name = f"{func_type}:{func.__name__}"
        new_stack = prev_stack + [current_name]
        
        # Save updated context - but preserve attempt counter from retry loop
        stack_token = call_stack_var.set(new_stack)
        func_token = current_func_var.set(current_name)
        index_token = current_index_var.set(new_index)
        attempt_token = None  # We're not changing the attempt value
        
        # Create a unique append_log function for this specific invocation
        if func_type == "task" and get_log_base_path() is not None:
            # Form file name base
            file_index = new_index.lstrip('_')
            
            # Create logging function for this invocation
            invocation_append_log = create_async_log_function(file_index)
            
            # Set this specific append_log in the context
            append_log_token = append_log_var.set(invocation_append_log)
            append_log_is_async_token = append_log_is_async_var.set(True)
        else:
            append_log_token = None
            append_log_is_async_token = None
        
        # Closures for context access
        def get_call_chain():
            return call_stack_var.get().copy()
        
        def get_current_index():
            return current_index_var.get()
        
        # Create a function with bound context for this specific invocation
        async def execute_with_context():
            # Create a new globals dictionary with the necessary additions
            local_globals = func.__globals__.copy()
            local_globals['call_chain'] = get_call_chain
            local_globals['get_current_index'] = get_current_index
            local_globals['append_log'] = append_log
            
            # Execute in isolated context
            func_copy = types.FunctionType(
                func.__code__, 
                local_globals,
                func.__name__, 
                func.__defaults__, 
                func.__closure__
            )
            return await func_copy(*args, **kwargs)
        
        try:
            return await execute_with_context()
        finally:
            # Restore previous context
            call_stack_var.reset(stack_token)
            current_func_var.reset(func_token)
            current_index_var.reset(index_token)
            if attempt_token:
                current_attempt_var.reset(attempt_token)
            if append_log_token:
                append_log_var.reset(append_log_token)
            if append_log_is_async_token:
                append_log_is_async_var.reset(append_log_is_async_token)
    
    def sync_wrapper(*args, **kwargs):
        # Save current context
        prev_stack = call_stack_var.get().copy()
        prev_func = current_func_var.get()
        prev_index = current_index_var.get()
        prev_attempt = current_attempt_var.get()
        prev_append_log = append_log_var.get()
        prev_append_log_is_async = append_log_is_async_var.get()
        
        # Generate new index
        if func_type == "flow" and not prev_func:  # First flow
            new_index = ""
        else:
            # Get next index for parent
            next_idx = get_next_index(prev_index)
            
            if func_type == "flow":
                new_index = f"{prev_index}_{next_idx}"
            else:  # task
                new_index = f"{prev_index}_{next_idx}_{func.__name__}"
        
        # Update context
        current_name = f"{func_type}:{func.__name__}"
        new_stack = prev_stack + [current_name]
        
        # Save updated context - but preserve attempt counter from retry loop
        stack_token = call_stack_var.set(new_stack)
        func_token = current_func_var.set(current_name)
        index_token = current_index_var.set(new_index)
        attempt_token = None  # We're not changing the attempt value
        
        # Create a unique append_log function for this specific invocation
        if func_type == "task" and get_log_base_path() is not None:
            # Form file name base
            file_index = new_index.lstrip('_')
            
            # Create logging function for this invocation
            invocation_append_log = create_sync_log_function(file_index)
            
            # Set this specific append_log in the context
            append_log_token = append_log_var.set(invocation_append_log)
            append_log_is_async_token = append_log_is_async_var.set(False)
        else:
            append_log_token = None
            append_log_is_async_token = None
        
        # Closures for context access
        def get_call_chain():
            return call_stack_var.get().copy()
        
        def get_current_index():
            return current_index_var.get()
        
        # Create a function with bound context for this specific invocation
        def execute_with_context():
            # Create a new globals dictionary with the necessary additions
            local_globals = func.__globals__.copy()
            local_globals['call_chain'] = get_call_chain
            local_globals['get_current_index'] = get_current_index
            local_globals['append_log'] = append_log
            
            # Execute in isolated context
            func_copy = types.FunctionType(
                func.__code__, 
                local_globals,
                func.__name__, 
                func.__defaults__, 
                func.__closure__
            )
            return func_copy(*args, **kwargs)
        
        try:
            return execute_with_context()
        finally:
            # Restore previous context
            call_stack_var.reset(stack_token)
            current_func_var.reset(func_token)
            current_index_var.reset(index_token)
            if attempt_token:
                current_attempt_var.reset(attempt_token)
            if append_log_token:
                append_log_var.reset(append_log_token)
            if append_log_is_async_token:
                append_log_is_async_var.reset(append_log_is_async_token)
    
    # Choose appropriate wrapper and save metadata
    wrapper = async_wrapper if is_async else sync_wrapper
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    wrapper.__doc__ = func.__doc__
    return wrapper


def flow(func: Callable) -> Callable:
    """Decorator for flow functions"""
    return create_wrapper(func, "flow")


def _task_impl(
    func: Optional[Callable] = None,
    *,
    retries: int = 1,
    retry_delay_seconds: RetryDelayType = 0,
    cache_on: Optional[Tuple[str, ...]] = None,
    semaphore: Optional[SemaphoreType] = None,
) -> Callable:
    """
    Internal implementation of the task decorator that handles both
    @task and @task() forms.
    """
    # If func is provided directly, this is the @task form
    if func is not None:
        # Apply the decorator with default arguments
        def decorator(decorated_func):
            # First, apply the create_wrapper to inject flow/task context
            flow_wrapped_func = create_wrapper(decorated_func, "task")
            
            function_name = decorated_func.__name__
            
            # Determine if the function is async
            is_async = asyncio.iscoroutinefunction(decorated_func)

            logging.debug(
                f"Decorating {'async' if is_async else 'sync'} function: {function_name}"
            )

            # Implementation for synchronous functions
            @functools.wraps(flow_wrapped_func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                global _active_tasks_count, _active_task_pictos
                task_id = "unknown"
                picto = hash_to_pictogram(task_id)

                with _active_tasks_lock:
                    _active_tasks_count += 1
                    if picto:
                        _active_task_pictos.append(picto)
                    active_tasks_count = _active_tasks_count
                    active_pictos_list = _active_task_pictos.copy()

                active_tasks_log = f"{active_tasks_count}"
                if 0 < active_tasks_count <= 4:
                    active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'

                logging.info(f"Executing sync task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}")

                # Function to execute with retry logic
                def execute_task() -> Any:
                    # Implement retry logic
                    for attempt in range(retries):
                        # Set the current attempt in context variable
                        current_attempt_var.set(attempt)
                        
                        try:
                            if attempt > 0:
                                logging.info(
                                    f"Retry {attempt}/{retries - 1} for {function_name}({picto} {task_id[:7]})"
                                )

                            # Execute the flow-wrapped function
                            result = flow_wrapped_func(*args, **kwargs)

                            logging.info(
                                f"Successfully completed {function_name}({picto} {task_id[:7]})"
                            )
                            return result
                        except Exception as e:
                            logging.warning(
                                f"Attempt {attempt + 1}/{retries} failed for {function_name}({picto} {task_id[:7]}): {e}"
                            )
                            # On the last attempt, raise the exception
                            if attempt == retries - 1:
                                logging.error(
                                    f"All {retries} attempts failed for {function_name}({picto} {task_id[:7]})"
                                )
                                raise

                            # Otherwise, wait before retrying
                            delay = 0  # Default delay is 0
                            if delay > 0:
                                logging.debug(
                                    f"Waiting {delay}s before retry {attempt + 2} for {function_name}({picto} {task_id[:7]})"
                                )
                                time.sleep(delay)

                try:
                    return execute_task()
                finally:
                    with _active_tasks_lock:
                        _active_tasks_count -= 1
                        if picto and picto in _active_task_pictos:
                            _active_task_pictos.remove(picto)
                        active_tasks_count = _active_tasks_count
                        active_pictos_list = _active_task_pictos.copy()

                    active_tasks_log = f"{active_tasks_count}"
                    if 0 < active_tasks_count <= 4:
                        active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'
                    
                    logging.info(f"Finished sync task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}")

            # Implementation for asynchronous functions
            @functools.wraps(flow_wrapped_func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                global _active_tasks_count, _active_task_pictos
                task_id = "unknown"
                picto = hash_to_pictogram(task_id)

                with _active_tasks_lock:
                    _active_tasks_count += 1
                    if picto:
                        _active_task_pictos.append(picto)
                    active_tasks_count = _active_tasks_count
                    active_pictos_list = _active_task_pictos.copy()
                
                active_tasks_log = f"{active_tasks_count}"
                if 0 < active_tasks_count <= 4:
                    active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'
                
                logging.info(f"Executing async task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}")

                # Apply semaphore if provided
                async def execute_task() -> Any:
                    # Implement retry logic
                    for attempt in range(retries):
                        # Set the current attempt in context variable
                        current_attempt_var.set(attempt)
                        
                        try:
                            if attempt > 0:
                                logging.info(
                                    f"Retry {attempt}/{retries - 1} for {function_name}({picto} {task_id[:7]})"
                                )

                            # Execute the flow-wrapped function
                            result = await flow_wrapped_func(*args, **kwargs)

                            logging.info(
                                f"Successfully completed {function_name}({picto} {task_id[:7]})"
                            )
                            return result
                        except Exception as e:
                            logging.warning(
                                f"Attempt {attempt + 1}/{retries} failed for {function_name}({picto} {task_id[:7]}): {e}"
                            )
                            # On the last attempt, raise the exception
                            if attempt == retries - 1:
                                logging.error(
                                    f"All {retries} attempts failed for {function_name}({picto} {task_id[:7]})"
                                )
                                raise

                            # Otherwise, wait before retrying
                            delay = 0  # Default delay is 0
                            if delay > 0:
                                logging.debug(
                                    f"Waiting {delay}s before retry {attempt + 2} for {function_name}({picto} {task_id[:7]})"
                                )
                                await asyncio.sleep(delay)

                try:
                    return await execute_task()
                finally:
                    with _active_tasks_lock:
                        _active_tasks_count -= 1
                        if picto and picto in _active_task_pictos:
                            _active_task_pictos.remove(picto)
                        active_tasks_count = _active_tasks_count
                        active_pictos_list = _active_task_pictos.copy()

                    active_tasks_log = f"{active_tasks_count}"
                    if 0 < active_tasks_count <= 4:
                        active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'

                    logging.info(f"Finished async task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}")

            # Return the appropriate wrapper based on whether the function is async
            return async_wrapper if is_async else sync_wrapper
        
        # Apply the decorator immediately with default parameters
        return decorator(func)
    
    # Otherwise, this is the @task() or @task(params) form
    # Implementation for the parametrized decorator
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # First, apply the create_wrapper to inject flow/task context
        flow_wrapped_func = create_wrapper(func, "task")
        
        function_name = func.__name__
        # Prepare function signature for extracting cache arguments
        sig = inspect.signature(func)

        # Determine if the function is async
        is_async = asyncio.iscoroutinefunction(func)

        logging.debug(
            f"Decorating {'async' if is_async else 'sync'} function: {function_name}"
        )

        # Validate semaphore type
        if semaphore is not None:
            if is_async and not isinstance(semaphore, asyncio.Semaphore):
                raise TypeError(
                    f"Async function {function_name} requires asyncio.Semaphore"
                )
            if not is_async and not isinstance(semaphore, threading.Semaphore):
                raise TypeError(
                    f"Sync function {function_name} requires threading.Semaphore"
                )

        # Implementation for synchronous functions
        @functools.wraps(flow_wrapped_func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Compute cache key based on specified arguments (including defaults)
            cache_key = None
            if cache_on and get_cache_base_path() is not None:
                bound_args = sig.bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                # Only cache if all specified argument names are provided
                if all(name in bound_args.arguments for name in cache_on):
                    cache_values = {name: bound_args.arguments[name] for name in cache_on}
                    cache_key = hash_json(cache_values)

            task_id = cache_key if cache_key is not None else "unknown"
            picto = hash_to_pictogram(task_id)
            
            global _active_tasks_count, _active_task_pictos
            with _active_tasks_lock:
                _active_tasks_count += 1
                if picto:
                    _active_task_pictos.append(picto)
                active_tasks_count = _active_tasks_count
                active_pictos_list = _active_task_pictos.copy()

            active_tasks_log = f"{active_tasks_count}"
            if 0 < active_tasks_count <= 4:
                active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'

            logging.info(f"Executing sync task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}")

            try:
                # Handle caching if enabled
                if cache_on and cache_key is not None and get_cache_base_path() is not None:
                    try:
                        cache_path = get_cache_path(function_name, cache_key)
                        cached_result = read_cache_sync(cache_path, function_name)
                        logging.info(f"Using cached result for {function_name}({picto} {task_id[:7]})")
                        return cached_result
                    except CacheMissError:
                        # This is expected if the cache doesn't exist yet
                        pass
                    except ValueError:
                        # If cache path not configured, skip cache
                        pass

                # Function to execute with retry logic
                def execute_task() -> Any:
                    # Implement retry logic
                    for attempt in range(retries):
                        # Set the current attempt in context variable
                        current_attempt_var.set(attempt)
                        
                        try:
                            if attempt > 0:
                                logging.info(
                                    f"Retry {attempt}/{retries - 1} for {function_name}({picto} {task_id[:7]})"
                                )

                            # Execute the flow-wrapped function
                            result = flow_wrapped_func(*args, **kwargs)

                            # Cache the result if enabled
                            if cache_on and cache_key is not None and get_cache_base_path() is not None:
                                try:
                                    cache_path = get_cache_path(function_name, cache_key)
                                    write_cache_sync(cache_path, result, function_name)
                                except ValueError:
                                    # If cache path not configured, skip cache
                                    pass

                            logging.info(
                                f"Successfully completed {function_name}({picto} {task_id[:7]})"
                            )
                            return result
                        except Exception as e:
                            logging.warning(
                                f"Attempt {attempt + 1}/{retries} failed for {function_name}({picto} {task_id[:7]}): {e}"
                            )
                            # On the last attempt, raise the exception
                            if attempt == retries - 1:
                                logging.error(
                                    f"All {retries} attempts failed for {function_name}({picto} {task_id[:7]})"
                                )
                                raise

                            # Otherwise, wait before retrying
                            delay = 0  # Default delay is 0
                            if delay > 0:
                                logging.debug(
                                    f"Waiting {delay}s before retry {attempt + 2} for {function_name}({picto} {task_id[:7]})"
                                )
                                time.sleep(delay)

                # Apply semaphore if provided
                if semaphore is not None:
                    logging.debug(
                        f"Acquiring sync semaphore for {function_name}({picto} {task_id[:7]})"
                    )
                    with semaphore:
                        logging.debug(
                            f"Acquired sync semaphore for {function_name}({picto} {task_id[:7]})"
                        )
                        return execute_task()
                else:
                    return execute_task()
            finally:
                with _active_tasks_lock:
                    _active_tasks_count -= 1
                    if picto and picto in _active_task_pictos:
                        _active_task_pictos.remove(picto)
                    active_tasks_count = _active_tasks_count
                    active_pictos_list = _active_task_pictos.copy()

                active_tasks_log = f"{active_tasks_count}"
                if 0 < active_tasks_count <= 4:
                    active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'

                logging.info(
                    f"Finished sync task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}"
                )

        # Implementation for asynchronous functions
        @functools.wraps(flow_wrapped_func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Compute cache key based on specified arguments (including defaults)
            cache_key = None
            if cache_on and get_cache_base_path() is not None:
                bound_args = sig.bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                # Only cache if all specified argument names are provided
                if all(name in bound_args.arguments for name in cache_on):
                    cache_values = {name: bound_args.arguments[name] for name in cache_on}
                    cache_key = hash_json(cache_values)

            task_id = cache_key if cache_key is not None else "unknown"
            picto = hash_to_pictogram(task_id)
            
            global _active_tasks_count, _active_task_pictos
            with _active_tasks_lock:
                _active_tasks_count += 1
                if picto:
                    _active_task_pictos.append(picto)
                active_tasks_count = _active_tasks_count
                active_pictos_list = _active_task_pictos.copy()
            
            active_tasks_log = f"{active_tasks_count}"
            if 0 < active_tasks_count <= 4:
                active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'

            logging.info(f"Executing async task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}")

            try:
                # Handle caching if enabled
                if cache_on and cache_key is not None and get_cache_base_path() is not None:
                    try:
                        cache_path = get_cache_path(function_name, cache_key)
                        cached_result = await read_cache_async(cache_path, function_name)
                        logging.info(f"Using cached result for {function_name}({picto} {task_id[:7]})")
                        return cached_result
                    except CacheMissError:
                        # This is expected if the cache doesn't exist yet
                        pass
                    except ValueError:
                        # If cache path not configured, skip cache
                        pass

                # Apply semaphore if provided
                async def execute_task() -> Any:
                    # Implement retry logic
                    for attempt in range(retries):
                        # Set the current attempt in context variable
                        current_attempt_var.set(attempt)
                        
                        try:
                            if attempt > 0:
                                logging.info(
                                    f"Retry {attempt}/{retries - 1} for {function_name}({picto} {task_id[:7]})"
                                )

                            # Execute the flow-wrapped function
                            result = await flow_wrapped_func(*args, **kwargs)

                            # Cache the result if enabled
                            if cache_on and cache_key is not None and get_cache_base_path() is not None:
                                try:
                                    cache_path = get_cache_path(function_name, cache_key)
                                    # Deepcopy result to prevent mutations from other async tasks
                                    # during serialization in the background thread.
                                    result_for_cache = copy.deepcopy(result)
                                    await write_cache_async(cache_path, result_for_cache, function_name)
                                except ValueError:
                                    # If cache path not configured, skip cache
                                    pass

                            logging.info(
                                f"Successfully completed {function_name}({picto} {task_id[:7]})"
                            )
                            return result
                        except Exception as e:
                            logging.warning(
                                f"Attempt {attempt + 1}/{retries} failed for {function_name}({picto} {task_id[:7]}): {e}"
                            )
                            # On the last attempt, raise the exception
                            if attempt == retries - 1:
                                logging.error(
                                    f"All {retries} attempts failed for {function_name}({picto} {task_id[:7]})"
                                )
                                raise

                            # Otherwise, wait before retrying
                            delay = 0  # Default delay is 0
                            if delay > 0:
                                logging.debug(
                                    f"Waiting {delay}s before retry {attempt + 2} for {function_name}({picto} {task_id[:7]})"
                                )
                                await asyncio.sleep(delay)

                if semaphore is not None:
                    logging.debug(
                        f"Acquiring async semaphore for {function_name}({picto} {task_id[:7]})"
                    )
                    async with semaphore:  # type: ignore
                        logging.debug(
                            f"Acquired async semaphore for {function_name}({picto} {task_id[:7]})"
                        )
                        return await execute_task()
                else:
                    return await execute_task()
            finally:
                with _active_tasks_lock:
                    _active_tasks_count -= 1
                    if picto and picto in _active_task_pictos:
                        _active_task_pictos.remove(picto)
                    active_tasks_count = _active_tasks_count
                    active_pictos_list = _active_task_pictos.copy()

                active_tasks_log = f"{active_tasks_count}"
                if 0 < active_tasks_count <= 4:
                    active_tasks_log = f'{active_tasks_count}: [{";".join(active_pictos_list)}]'

                logging.info(
                    f"Finished async task {function_name}({picto} {task_id[:7]}). Active tasks: {active_tasks_log}"
                )

        # Return the appropriate wrapper based on whether the function is async
        return async_wrapper if is_async else sync_wrapper

    return decorator


# Public task decorator that can be used with or without parentheses
def task(
    func=None, 
    *,
    retries=1, 
    retry_delay_seconds: RetryDelayType = 0, 
    cache_on=None, 
    semaphore=None
):
    """
    A decorator for handling both synchronous and asynchronous tasks with retry, caching,
    and semaphore mechanisms. Can be used both with and without parentheses.
    
    Usage:
        @task  # Without parentheses
        def my_func():
            pass
            
        @task()  # With empty parentheses
        def my_func():
            pass
            
        @task(retries=3)  # With parameters
        def my_func():
            pass

    Args:
        retries: Total number of attempts (including the first try)
        retry_delay_seconds: Delay between retries in seconds (int or function that takes try number and returns delay)
        cache_on: Tuple of argument names to include in cache key hash
        semaphore: Optional semaphore for limiting concurrent executions
                  (asyncio.Semaphore for async functions, threading.Semaphore for sync functions)
    """
    return _task_impl(
        func, 
        retries=retries, 
        retry_delay_seconds=retry_delay_seconds, 
        cache_on=cache_on, 
        semaphore=semaphore
    ) 