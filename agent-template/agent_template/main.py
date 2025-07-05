import asyncio
from dotenv import load_dotenv
from pathlib import Path
from taskman import configure_cache_path, configure_log_path
from .flows.main_flow import main_flow
import logging
import sys
from time import time
from os import environ
import os

def main():
    """
    Main entry point for the agent template application.
    Loads environment variables and runs the main flow.
    """
    load_dotenv()
    
    # --- Setup Logging and Caching ---
    run_id = f"helloworld_run_{time()}"
    environ["TASK_ID"] = run_id
    
    # Configure cache and log paths
    cache_dir = Path(f"./.cache/{run_id}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    configure_cache_path(cache_dir)
    
    logs_dir = Path(f"./.log/{run_id}")
    logs_dir.mkdir(parents=True, exist_ok=True)
    configure_log_path(logs_dir)

    # Configure logging
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    log_format = "[%(asctime)s] %(levelname)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    root_logger.addHandler(handler)

    try:
        asyncio.run(main_flow())
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
