import asyncio
import logging
import random
import threading
import time
from pathlib import Path

from taskman import task, configure_cache_path


# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Настройка пути для кеша
configure_cache_path(Path("./.cache"))


# Example 1: Simple synchronous task with retries
@task(retries=3, retry_delay_seconds=1)
def fetch_data(url: str) -> dict:
    """Simulate fetching data from a URL with possible failures."""
    # Simulate random failure (30% chance)
    if random.random() < 0.3:
        print(f"Failed to fetch data from {url}, retrying...")
        raise ConnectionError("Connection failed")

    print(f"Successfully fetched data from {url}")
    return {"data": f"Content from {url}", "timestamp": time.time()}


# Example 2: Async task with retries and exponential backoff
@task(
    retries=5,
    retry_delay_seconds=lambda attempt: 2**attempt,  # Exponential backoff
)
async def fetch_async_data(url: str) -> dict:
    """Simulate fetching data asynchronously with exponential backoff."""
    # Simulate random failure (30% chance)
    if random.random() < 0.3:
        print(f"Failed to fetch async data from {url}, retrying...")
        raise ConnectionError("Async connection failed")

    # Simulate network delay
    await asyncio.sleep(0.5)
    print(f"Successfully fetched async data from {url}")
    return {"data": f"Async content from {url}", "timestamp": time.time()}


# Example 3: Cached task based on ID
@task(
    cache_on=("computation_id","iterations")
)
def expensive_computation(computation_id: str, iterations: int = 1000000) -> int:
    """Simulate an expensive computation that we want to cache."""
    print(f"Running expensive computation {computation_id}...")

    # Simulate computation
    result = sum(i * i for i in range(iterations))

    print(f"Completed computation {computation_id}")
    return result


# Example 4: Async task with semaphore to limit concurrency
async def run_limited_concurrent_async_tasks():
    """Run multiple async tasks with limited concurrency using an async semaphore."""
    # Create a semaphore allowing only 2 concurrent executions
    semaphore = asyncio.Semaphore(2)

    @task(semaphore=semaphore)
    async def limited_async_task(task_id: int) -> str:
        print(f"Starting async task {task_id}")
        await asyncio.sleep(1)  # Simulate work
        print(f"Finished async task {task_id}")
        return f"Result from async task {task_id}"

    # Run 5 tasks concurrently, but limited to 2 at a time by the semaphore
    tasks = [limited_async_task(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    return results


# Example 5: Sync task with semaphore to limit concurrency
def run_limited_concurrent_sync_tasks():
    """Run multiple sync tasks with limited concurrency using a threading semaphore."""
    # Create a semaphore allowing only 2 concurrent executions
    semaphore = threading.Semaphore(2)
    results = []

    @task(semaphore=semaphore)
    def limited_sync_task(task_id: int) -> str:
        print(f"Starting sync task {task_id}")
        time.sleep(1)  # Simulate work
        print(f"Finished sync task {task_id}")
        return f"Result from sync task {task_id}"

    # Run 5 tasks, limited to 2 at a time by the semaphore
    for i in range(5):
        result = limited_sync_task(i)
        results.append(result)

    return results


# Example 6: Change logging level for specific section
def demo_logging_levels():
    """Demonstrate different logging levels."""
    print("\n=== Demonstrating logging levels ===")

    # First run with INFO level (default)
    print("Running with INFO level:")

    @task(retries=2)
    def simple_task(task_id: str) -> str:
        if task_id == "fail":
            raise ValueError("Simulated failure")
        return f"Result: {task_id}"

    # Run successfully
    result = simple_task("success")
    print(f"Result: {result}")

    # Now switch to DEBUG level to see more details
    print("\nSwitching to DEBUG level:")
    logging.getLogger().setLevel(logging.DEBUG)

    try:
        # This will fail and retry
        simple_task("fail")
    except ValueError:
        print("Task failed after retries (expected)")

    # Return to INFO level
    logging.getLogger().setLevel(logging.INFO)


async def main():
    print("=== Running examples with logging ===")

    # Example 1: Run the synchronous task
    try:
        result1 = fetch_data("https://example.com/api/data")
        print(f"Result: {result1}\n")
    except Exception as e:
        print(f"Failed after retries: {e}\n")

    # Example 2: Run the async task
    try:
        result2 = await fetch_async_data("https://example.com/api/async-data")
        print(f"Async result: {result2}\n")
    except Exception as e:
        print(f"Async task failed after retries: {e}\n")

    # Example 3: Run cached computation twice - second run should use cache
    result3_first = expensive_computation("task1")
    print(f"First computation result: {result3_first}")

    # This should use the cached result
    result3_second = expensive_computation("task1")
    print(f"Second computation result (from cache): {result3_second}\n")

    result3_second_another_iterations = expensive_computation("task1", 2000000)
    print(f"Second computation with another number of iterations: {result3_second_another_iterations}\n")

    # Different ID will run the computation again
    result3_third = expensive_computation("task2")
    print(f"Third computation result (different ID): {result3_third}\n")

    # Example 4: Run limited concurrent async tasks
    results4 = await run_limited_concurrent_async_tasks()
    print(f"Limited concurrent async tasks results: {results4}\n")

    # Example 5: Run limited concurrent sync tasks
    results5 = run_limited_concurrent_sync_tasks()
    print(f"Limited concurrent sync tasks results: {results5}\n")

    # Example 6: Demonstrate logging levels
    demo_logging_levels()


if __name__ == "__main__":
    asyncio.run(main())
