import asyncio
import base64
import logging
import os
import pathlib
from typing import Optional

import aiohttp
from dotenv import load_dotenv

load_dotenv()

DATALAB_API_KEY = os.getenv("DATALAB_API_KEY")
DATALAB_API_BASE = "https://www.datalab.to/api/v1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_pdf_with_datalab(
    pdf_path: str | pathlib.Path,
    output_dir: str | pathlib.Path,
    use_llm: bool = True,
    max_pages: int = 100,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Processes a PDF file using the Datalab.to Marker API, saves the output,
    and returns the markdown content.

    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Path to the directory where output markdown and images will be saved.
        use_llm: Whether to use an LLM for enhanced accuracy. Defaults to True.
        max_pages: Maximum number of pages to process. Defaults to 100.
        api_key: Datalab.to API key. If not provided, it's read from the DATALAB_API_KEY env var.

    Returns:
        The markdown content of the processed PDF, or None if an error occurred.
    """
    pdf_path = pathlib.Path(pdf_path)
    output_dir = pathlib.Path(output_dir)

    api_key = api_key or DATALAB_API_KEY
    if not api_key:
        logger.error("DATALAB_API_KEY environment variable not set.")
        raise ValueError("Datalab API key is required.")

    if not pdf_path.exists():
        logger.error(f"Input file not found: {pdf_path}")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    url = f"{DATALAB_API_BASE}/marker"
    headers = {"X-Api-Key": api_key}

    form_data = aiohttp.FormData()
    form_data.add_field('file', pdf_path.read_bytes(), filename=pdf_path.name, content_type='application/pdf')
    form_data.add_field('use_llm', str(use_llm))
    form_data.add_field('max_pages', str(max_pages))
    form_data.add_field('output_format', 'markdown')

    async with aiohttp.ClientSession() as session:
        try:
            # Initial request
            logger.info(f"Uploading {pdf_path.name} to Datalab.to for processing...")
            async with session.post(url, data=form_data, headers=headers) as response:
                response.raise_for_status()
                initial_data = await response.json()

            if not initial_data.get("success"):
                logger.error(f"API request failed: {initial_data.get('error')}")
                return None

            check_url = initial_data["request_check_url"]
            logger.info(f"File uploaded. Polling for results at {check_url}")

            # Polling for results
            max_polls = 300
            for i in range(max_polls):
                await asyncio.sleep(5)  # Wait 5 seconds between polls
                async with session.get(check_url, headers=headers) as check_response:
                    check_response.raise_for_status()
                    data = await check_response.json()

                    if data.get("status") == "complete":
                        logger.info("Processing complete.")
                        if data.get("success"):
                            markdown_content = data.get("markdown", "")
                            
                            # Save markdown to file
                            article_path = output_dir / "article.md"
                            article_path.write_text(markdown_content, encoding='utf-8')
                            logger.info(f"Markdown content saved to {article_path}")

                            # Save images
                            images = data.get("images", {})
                            if images:
                                logger.info(f"Saving {len(images)} images...")
                                for img_name, img_data in images.items():
                                    img_path = output_dir / img_name
                                    try:
                                        img_bytes = base64.b64decode(img_data)
                                        img_path.write_bytes(img_bytes)
                                        logger.info(f"Saved image {img_name}")
                                    except Exception as e:
                                        logger.error(f"Failed to decode or save image {img_name}: {e}")
                            
                            return markdown_content
                        else:
                            logger.error(f"Processing failed: {data.get('error')}")
                            return None
                    else:
                        logger.info(f"Still processing... (poll {i+1}/{max_polls})")

            logger.error("Polling timed out after 300 attempts.")
            return None

        except aiohttp.ClientError as e:
            logger.error(f"An HTTP error occurred: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None 