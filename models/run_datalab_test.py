#!/usr/bin/env python
import asyncio
import os
import pathlib
import shutil
import logging

from dotenv import load_dotenv

# It's better to add the project root to sys.path or use editable installs,
# but for a simple script, this relative import works if run from the project root.
try:
    from models.datalab import process_pdf_with_datalab
except (ModuleNotFoundError, ImportError):
    # If the script is run from the `models` directory, this will work
    from datalab import process_pdf_with_datalab


# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
# The script will look for a .env file in the current directory or parent directories.
# Make sure you have a .env file in the `models` directory or the project root.
load_dotenv()

DATALAB_API_KEY = os.getenv("DATALAB_API_KEY")

# Define paths relative to the project root
# The script assumes it's being run from the root of the 'uneditor-ethcannes' project
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
NOTEBOOK_DIR = PROJECT_ROOT / "notebook"
INPUT_PDF = NOTEBOOK_DIR / "2019-953.pdf"
OUTPUT_DIR = NOTEBOOK_DIR / "datalab" / "2019-953"


async def main():
    """
    Runs a test of the PDF processing flow with the Datalab.to API.
    """
    logging.info("--- Starting Datalab.to PDF Processing Test Script ---")

    if not DATALAB_API_KEY:
        logging.error("FATAL: DATALAB_API_KEY environment variable not set.")
        logging.error("Please create a .env file in the 'models' directory or project root with the key.")
        return

    if not INPUT_PDF.exists():
        logging.error(f"FATAL: Input PDF not found at {INPUT_PDF}")
        return

    # Clean up previous run's output directory if it exists
    if OUTPUT_DIR.exists():
        logging.warning(f"Removing existing output directory: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    logging.info(f"Processing file: {INPUT_PDF}")
    logging.info(f"Output will be saved to: {OUTPUT_DIR}")

    try:
        # Run the processing function
        markdown_output = await process_pdf_with_datalab(
            pdf_path=INPUT_PDF,
            output_dir=OUTPUT_DIR
        )

        # --- Verification ---
        logging.info("--- Verifying Results ---")
        errors = []

        # 1. Check if the function returns markdown content
        if not markdown_output or not isinstance(markdown_output, str) or len(markdown_output) == 0:
            errors.append("Test FAILED: The function did not return valid markdown content.")
        else:
            logging.info("Check PASSED: Function returned markdown content.")

        # 2. Check if the output directory was created
        if not OUTPUT_DIR.exists() or not OUTPUT_DIR.is_dir():
            errors.append(f"Test FAILED: Output directory was not created at {OUTPUT_DIR}.")
        else:
            logging.info("Check PASSED: Output directory created.")

        # 3. Check if the article.md file was created and is not empty
        article_file = OUTPUT_DIR / "article.md"
        if not article_file.exists() or article_file.stat().st_size == 0:
            errors.append("Test FAILED: article.md was not created or is empty.")
        else:
            logging.info("Check PASSED: article.md created and is not empty.")

        # 4. Check if image files were created
        image_files = list(OUTPUT_DIR.glob("*.jpeg")) + list(OUTPUT_DIR.glob("*.jpg")) + list(OUTPUT_DIR.glob("*.png"))
        if not image_files:
            errors.append("Test FAILED: No image files were found in the output directory.")
        else:
            logging.info(f"Check PASSED: Found {len(image_files)} image file(s).")

        # --- Summary ---
        if errors:
            logging.error("\n--- Test Completed with Errors ---")
            for error in errors:
                logging.error(error)
        else:
            logging.info("\n--- Test Completed Successfully! All checks passed. ---")

    except Exception as e:
        logging.error(f"An unexpected error occurred during the test: {e}", exc_info=True)

    finally:
        # Ask user if they want to clean up the directory
        # This allows inspection of the results after the test run
        if OUTPUT_DIR.exists():
            cleanup = input(f"Do you want to remove the output directory '{OUTPUT_DIR}'? [y/N]: ")
            if cleanup.lower() == 'y':
                shutil.rmtree(OUTPUT_DIR)
                logging.info("Cleaned up output directory.")


if __name__ == "__main__":
    asyncio.run(main()) 