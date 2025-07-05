#!/usr/bin/env python
import asyncio
import time
from pathlib import Path
import logging
import random

from taskman import flow, task, configure_log_path, configure_cache_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configure path for log and cache
LOG_DIR = Path("./.log")
CACHE_DIR = Path("./.cache")

# Basic synchronous example
@flow
def sync_flow_example():
    """Example of a synchronous flow"""
    logging.info(f"Current call chain: {call_chain()}")
    logging.info(f"Current index: {get_current_index()}")
    
    result1 = process_item(1)
    result2 = process_item(2)
    
    return summarize_results_sync(result1 + result2)

# Using @task without parentheses
@task
def process_item(item):
    """Process a single item synchronously"""
    logging.info(f"Processing item {item}")
    append_log(f"Processing item {item} synchronously")
    return item * 10

# Using @task() with parentheses
@task()
def summarize_results_sync(value):
    """Summarize results synchronously"""
    append_log(f"Summarizing results: {value}")
    return f"Total: {value}"

# Asynchronous example with nested flows
@flow
async def main_flow():
    """Main asynchronous flow that coordinates other flows and tasks"""
    logging.info(f"Current call chain: {call_chain()}")
    logging.info(f"Current index: {get_current_index()}")
    
    # Create and gather multiple tasks
    task1 = asyncio.create_task(process_data(5))
    task2 = asyncio.create_task(process_data(10))
    
    # Wait for both tasks to complete
    results = await asyncio.gather(task1, task2)
    
    # Process the combined results
    final_result = await finalize_results(results[0] + results[1])
    
    return final_result

@flow
async def process_data(value):
    """Process data asynchronously, demonstrating a nested flow"""
    logging.info(f"Processing data in nested flow: {value}")
    logging.info(f"Current call chain: {call_chain()}")
    
    # Chain of async tasks
    transformed = await transform_data(value)
    validated = await validate_data(transformed)
    
    return validated

# Using @task without parentheses
@task
async def transform_data(value):
    """Transform data asynchronously"""
    await append_log(f"Transforming data: {value}")
    await asyncio.sleep(0.5)  # Simulate async operation
    return value * 2

# Using @task() with parentheses
@task()
async def validate_data(value):
    """Validate data asynchronously"""
    await append_log(f"Validating data: {value}")
    await asyncio.sleep(0.3)  # Simulate async operation
    return value + 5

# Using @task without parentheses
@task
async def finalize_results(total):
    """Finalize the combined results"""
    await append_log(f"Finalizing results: {total}")
    await asyncio.sleep(0.2)  # Simulate async operation
    return f"Final result: {total}"

# Example with retries and caching
@flow
async def advanced_flow():
    """Example flow with retries and caching"""
    result1 = await cached_operation("data1", retries=2)
    result2 = await cached_operation("data2", retries=1)
    return f"Advanced results: {result1}, {result2}"

# Using @task with parameters
@task(retries=3, retry_delay_seconds=1, cache_on=("data_key",))
async def cached_operation(data_key, retries=1):
    """Task that demonstrates caching and retry behavior"""
    await append_log(f"Running cached operation with key: {data_key}, retry setting: {retries}")
    
    # Simulate occasional failures to demonstrate retries
    if data_key == "data1" and retries > 0:
        # This will succeed on retry
        await append_log(f"Simulating failure for {data_key}")
        raise ValueError(f"Simulated error for {data_key}")
    
    await asyncio.sleep(0.5)
    
    return f"Processed {data_key}"

# Complex branching flow example with deep nesting (5 levels)
@flow
async def complex_flow(data_size=10):
    """
    Complex flow with deep nesting and parallel execution
    Level 1 - Root flow
    """
    logging.info(f"Starting complex flow with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Create two parallel branch flows
    branch_a_task = asyncio.create_task(branch_flow_a(data_size))
    branch_b_task = asyncio.create_task(branch_flow_b(data_size))
    
    # Wait for all branches to complete
    branch_a_result, branch_b_result = await asyncio.gather(branch_a_task, branch_b_task)
    
    # Aggregate results from all branches
    final_result = await aggregate_results({
        "branch_a": branch_a_result,
        "branch_b": branch_b_result
    })
    
    return final_result

@flow
async def branch_flow_a(data_size):
    """
    Branch A processing
    Level 2 - First branch
    """
    logging.info(f"Processing branch A with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Split processing across sub-branches
    half_size = data_size // 2
    
    # Create two parallel sub-branches
    sub_a1_task = asyncio.create_task(sub_branch_flow_a1(half_size))
    sub_a2_task = asyncio.create_task(sub_branch_flow_a2(half_size))
    
    # Wait for sub-branches to complete
    results = await asyncio.gather(sub_a1_task, sub_a2_task)
    
    # Merge results from sub-branches
    merged_result = results[0] + results[1]
    return merged_result

@flow
async def branch_flow_b(data_size):
    """
    Branch B processing
    Level 2 - Second branch
    """
    logging.info(f"Processing branch B with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Split processing across sub-branches
    half_size = data_size // 2
    
    # Create two parallel sub-branches with different processing logic
    sub_b1_task = asyncio.create_task(sub_branch_flow_b1(half_size))
    sub_b2_task = asyncio.create_task(sub_branch_flow_b2(half_size))
    
    # Wait for sub-branches to complete
    results = await asyncio.gather(sub_b1_task, sub_b2_task)
    
    # Merge results from sub-branches with special processing
    merged_result = results[0] * results[1]
    return merged_result

@flow
async def sub_branch_flow_a1(data_size):
    """
    Sub-branch A1 processing
    Level 3 - Sub-branch of A
    """
    logging.info(f"Processing sub-branch A1 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Create parallel leaf flows
    leaf_a1_1_task = asyncio.create_task(leaf_flow_a1_1(data_size))
    leaf_a1_2_task = asyncio.create_task(leaf_flow_a1_2(data_size))
    
    # Wait for leaf flows to complete
    results = await asyncio.gather(leaf_a1_1_task, leaf_a1_2_task)
    
    # Sum results
    return sum(results)

@flow
async def sub_branch_flow_a2(data_size):
    """
    Sub-branch A2 processing
    Level 3 - Sub-branch of A
    """
    logging.info(f"Processing sub-branch A2 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Process sequentially
    result1 = await leaf_flow_a2_1(data_size)
    result2 = await leaf_flow_a2_2(data_size)
    
    # Average results
    return (result1 + result2) / 2

@flow
async def sub_branch_flow_b1(data_size):
    """
    Sub-branch B1 processing
    Level 3 - Sub-branch of B
    """
    logging.info(f"Processing sub-branch B1 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Create multiple tasks with different parameters
    tasks = [
        asyncio.create_task(leaf_flow_b1_1(data_size, i))
        for i in range(3)
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Return the maximum result
    return max(results)

@flow
async def sub_branch_flow_b2(data_size):
    """
    Sub-branch B2 processing
    Level 3 - Sub-branch of B
    """
    logging.info(f"Processing sub-branch B2 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Create two parallel leaf flows
    leaf_b2_1_task = asyncio.create_task(leaf_flow_b2_1(data_size))
    leaf_b2_2_task = asyncio.create_task(leaf_flow_b2_2(data_size))
    
    # Wait for leaf flows to complete
    results = await asyncio.gather(leaf_b2_1_task, leaf_b2_2_task)
    
    # Minimum result plus fixed value
    return min(results) + 5

@flow
async def leaf_flow_a1_1(data_size):
    """
    Leaf flow A1-1
    Level 4 - Leaf of A1
    """
    logging.info(f"Processing leaf A1-1 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Execute several tasks in parallel
    tasks = [
        asyncio.create_task(process_leaf_item_a(f"A1-1-{i}", data_size))
        for i in range(3)
    ]
    
    results = await asyncio.gather(*tasks)
    return sum(results)

@flow
async def leaf_flow_a1_2(data_size):
    """
    Leaf flow A1-2
    Level 4 - Leaf of A1
    """
    logging.info(f"Processing leaf A1-2 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    result = await deep_task_a(data_size, "A1-2-special")
    return result * 2

@flow
async def leaf_flow_a2_1(data_size):
    """
    Leaf flow A2-1
    Level 4 - Leaf of A2
    """
    logging.info(f"Processing leaf A2-1 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Execute deepest level task
    result = await deepest_level_task_a("A2-1", data_size)
    return result

@flow
async def leaf_flow_a2_2(data_size):
    """
    Leaf flow A2-2
    Level 4 - Leaf of A2
    """
    logging.info(f"Processing leaf A2-2 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Execute sequential deep tasks and combine results
    part1 = await deep_task_a(data_size // 2, "A2-2-part1")
    part2 = await deep_task_a(data_size // 2, "A2-2-part2")
    
    return part1 + part2

@flow
async def leaf_flow_b1_1(data_size, variant):
    """
    Leaf flow B1-1
    Level 4 - Leaf of B1
    """
    logging.info(f"Processing leaf B1-1 variant {variant} with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    result = await deep_task_b(data_size, f"B1-1-v{variant}")
    return result * (variant + 1)  # Scale by variant

@flow
async def leaf_flow_b2_1(data_size):
    """
    Leaf flow B2-1
    Level 4 - Leaf of B2
    """
    logging.info(f"Processing leaf B2-1 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Execute a chain of deep tasks
    result = await deep_task_b(data_size, "B2-1-first")
    result = await deepest_level_task_b("B2-1-second", result)
    
    return result

@flow
async def leaf_flow_b2_2(data_size):
    """
    Leaf flow B2-2
    Level 4 - Leaf of B2
    """
    logging.info(f"Processing leaf B2-2 with data_size={data_size}")
    logging.info(f"Call chain: {call_chain()}")
    
    # Execute multiple tasks in parallel
    tasks = []
    for i in range(2):
        tasks.append(asyncio.create_task(deepest_level_task_b(f"B2-2-{i}", data_size)))
    
    results = await asyncio.gather(*tasks)
    return sum(results) / len(results)  # Average

# Mixing decorator styles to demonstrate flexibility
@task  # Without parentheses
async def process_leaf_item_a(item_id, value):
    """
    Process an individual item in branch A
    Level 5 - Task
    """
    await append_log(f"Processing leaf item A: {item_id} with value {value}")
    await asyncio.sleep(0.1)  # Simulate work
    return value + len(item_id)

@task  # Without parentheses
async def deep_task_a(value, task_id):
    """
    Deep task in branch A
    Level 5 - Task
    """
    await append_log(f"Executing deep task A: {task_id} with value {value}")
    await asyncio.sleep(0.2)
    return value * 1.5

@task()  # With parentheses
async def deep_task_b(value, task_id):
    """
    Deep task in branch B
    Level 5 - Task
    """
    await append_log(f"Executing deep task B: {task_id} with value {value}")
    await asyncio.sleep(0.15)
    return value * 2

@task  # Without parentheses
async def deepest_level_task_a(task_id, value):
    """
    Deepest level task in branch A
    Level 5 - Task
    """
    await append_log(f"Executing deepest level task A: {task_id} with value {value}")
    await asyncio.sleep(0.25)
    return value * 3 + random.randint(1, 10)

@task()  # With parentheses
async def deepest_level_task_b(task_id, value):
    """
    Deepest level task in branch B
    Level 5 - Task
    """
    await append_log(f"Executing deepest level task B: {task_id} with value {value}")
    await asyncio.sleep(0.3)
    return value * 1.75 + random.randint(1, 5)

@task  # Without parentheses
async def aggregate_results(result_dict):
    """
    Aggregate results from all branches
    """
    await append_log(f"Aggregating results: {result_dict}")
    await asyncio.sleep(0.2)
    
    # Calculate overall result
    total = 0
    for branch, value in result_dict.items():
        await append_log(f"Branch {branch} contributed {value}")
        total += value
    
    return {
        "total": total,
        "details": result_dict,
        "branches": len(result_dict)
    }

async def run_examples():
    """Run all examples and demonstrate differences"""
    # Configure paths for logs and cache
    configure_log_path(LOG_DIR)
    configure_cache_path(CACHE_DIR)
    
    # Create directories if they don't exist
    LOG_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    
    print("Running synchronous example...")
    try:
        sync_result = sync_flow_example()
        print(f"Sync result: {sync_result}")
    except Exception as e:
        print(f"Error in sync flow: {e}")
    
    print("\nRunning main asynchronous flow...")
    try:
        async_result = await main_flow()
        print(f"Async result: {async_result}")
    except Exception as e:
        print(f"Error in main flow: {e}")
    
    print("\nRunning advanced flow with retries and caching...")
    try:
        advanced_result = await advanced_flow()
        print(f"Advanced result: {advanced_result}")
        
        # Run again to demonstrate caching
        print("\nRunning advanced flow again (should use cache)...")
        advanced_result2 = await advanced_flow()
        print(f"Advanced result (cached): {advanced_result2}")
    except Exception as e:
        print(f"Error in advanced flow: {e}")
    
    print("\nRunning complex branching flow with deep nesting...")
    try:
        start_time = time.time()
        complex_result = await complex_flow(5)
        duration = time.time() - start_time
        print(f"Complex flow result: {complex_result}")
        print(f"Complex flow duration: {duration:.2f} seconds")
        print("The call stack logs show the nested execution pattern.")
    except Exception as e:
        print(f"Error in complex flow: {e}")
    
    print("\nExamples completed. Check the logs directory for call path logs.")

if __name__ == "__main__":
    asyncio.run(run_examples())
