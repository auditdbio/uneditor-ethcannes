import asyncio
from typing import List, Tuple
from taskman import flow
from ..tasks.geography_expert import geography_expert_task
from ..tasks.world_classifier import world_classifier_task
from asyncio import gather, create_task

async def single_object_pipeline() -> Tuple[str, str]:
    """Runs the full expert -> classifier pipeline for a single object."""
    # Get the description from the expert
    object_name = await geography_expert_task()
    
    # Classify the description
    world = await world_classifier_task(object_name)
    
    return object_name, world

@flow
async def main_flow():
    """
    Main flow that runs 5 geography classification pipelines in parallel.
    """

    print("Starting geography classification for 5 objects...")
    
    # Create and run the pipelines in parallel
    pipeline_tasks = [create_task(single_object_pipeline()) for _ in range(5)]
    results = await gather(*pipeline_tasks)
    
    # Print the results
    print("\n--- Classification Results ---")
    for object_name, world in results:
        print(f"- {object_name}: {world.capitalize()} World")
    print("--------------------------") 