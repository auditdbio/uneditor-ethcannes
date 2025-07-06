import asyncio
import hashlib
import logging
import pathlib
import re
import shutil
import uuid

import aiofiles
import aiohttp
import jinja2
from models.chat import ChatClient
from models.datalab import process_pdf_with_datalab
from models import chat_completions

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ScienceChatOrchestrator:
    """
    Orchestrates the lifecycle of a scientific chat session. Handles commands,
    document processing (download, parsing, distillation), and regular chat.
    Implements a file-based cache to avoid reprocessing PDFs.
    """

    def __init__(self, chat_client: ChatClient, model_name: str = "grok-3-mini-high", api_base_url: str = "http://localhost:8000"):
        self.chat_client = chat_client
        self.model = model_name
        self.distillation_model = "grok-3-mini-high"
        self.api_base_url = api_base_url

        self.cache_dir = pathlib.Path("agent_cache")
        self.temp_dir = self.cache_dir / "temp"
        self.papers_dir = self.cache_dir / "papers"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.papers_dir.mkdir(parents=True, exist_ok=True)

        self._load_unredactor_prompt()

    def _load_unredactor_prompt(self):
        """Loads the distillation prompt template from the file."""
        template_dir = pathlib.Path(__file__).parent / "prompts"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        self.unredactor_template = env.get_template("unredactor.j2")

    async def _download_pdf(self, url: str) -> pathlib.Path:
        """Downloads a PDF from a URL to a temporary directory."""
        temp_pdf_path = self.temp_dir / f"{uuid.uuid4()}.pdf"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                async with aiofiles.open(temp_pdf_path, 'wb') as f:
                    await f.write(await response.read())
        return temp_pdf_path

    async def _get_file_hash(self, file_path: pathlib.Path) -> str:
        """Computes the SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _filter_markdown_images(self, markdown_text: str, chat_uuid: str, paper_hash: str) -> str:
        """Replaces local image paths in markdown with full API URLs."""
        # This regex finds markdown images like ![...](images/figure1.png)
        # and captures the image name "figure1.png"
        pattern = r"!\[(.*?)\]\((?:images/)?(.*?)\)"
        
        def replace_func(match):
            image_name = match.group(2)
            new_url = f"{self.api_base_url}/v1/images/{chat_uuid}/{paper_hash}/{image_name}"
            return f"![{match.group(1)}]({new_url})"

        return re.sub(pattern, replace_func, markdown_text)

    async def _distill_text(self, paper_content: str) -> str:
        """Generates a distilled version of the paper using an LLM."""
        user_prompt = self.unredactor_template.render(paper=paper_content)
        system_prompt = "You are a Master Educator and Technical Author. Your task is to take a dense, raw academic paper and transform it into a lucid, self-contained technical monograph."
        
        distilled_content = await chat_completions(
            model=self.distillation_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        return distilled_content

    async def _handle_load_command(self, chat_uuid: str, url: str, user_input: str) -> dict:
        """Orchestrates the full PDF processing pipeline, using a cache."""
        try:
            # Add user command to history
            self.chat_client.add_message_to_history(chat_uuid, {"role": "user", "content": user_input})

            # 1. Download PDF and compute hash
            temp_pdf_path = await self._download_pdf(url)
            paper_hash = await self._get_file_hash(temp_pdf_path)
            
            paper_cache_dir = self.papers_dir / paper_hash
            raw_md_path = paper_cache_dir / "raw.md"
            distilled_md_path = paper_cache_dir / "distilled.md"
            images_dir = paper_cache_dir / "images"

            # 2. Check cache
            if paper_cache_dir.exists():
                logging.info(f"Cache hit for paper hash: {paper_hash}")
                async with aiofiles.open(raw_md_path, 'r', encoding='utf-8') as f:
                    raw_markdown = await f.read()
                async with aiofiles.open(distilled_md_path, 'r', encoding='utf-8') as f:
                    distilled_markdown = await f.read()
            else:
                logging.info(f"Cache miss for paper hash: {paper_hash}. Processing from scratch.")
                # 3. Cache Miss: Process from scratch
                paper_cache_dir.mkdir()
                
                # Run Datalab to get raw markdown and images
                datalab_output_dir = paper_cache_dir / "datalab_temp"
                raw_markdown = await process_pdf_with_datalab(temp_pdf_path, datalab_output_dir)
                if not raw_markdown:
                    raise ValueError("Failed to parse PDF with Datalab.")
                
                # Move images to the correct cache location
                if (datalab_output_dir / "images").exists():
                    shutil.move(str(datalab_output_dir / "images"), str(images_dir))
                
                # Distill text
                distilled_markdown = await self._distill_text(raw_markdown)

                # Save to cache
                async with aiofiles.open(raw_md_path, 'w', encoding='utf-8') as f:
                    await f.write(raw_markdown)
                async with aiofiles.open(distilled_md_path, 'w', encoding='utf-8') as f:
                    await f.write(distilled_markdown)
            
            temp_pdf_path.unlink() # Clean up downloaded temp file

            # 4. Filter markdown to insert correct, session-specific image URLs
            session_raw_md = self._filter_markdown_images(raw_markdown, chat_uuid, paper_hash)
            session_distilled_md = self._filter_markdown_images(distilled_markdown, chat_uuid, paper_hash)

            # 5. Add both versions to RAG context for the current session
            await self.chat_client.add_document(chat_uuid, session_raw_md)
            await self.chat_client.add_document(chat_uuid, session_distilled_md)

            # 6. Add assistant confirmation to history and return distilled text for display
            assistant_message = "I have finished processing the paper. Both the original and the distilled versions are now in my context. Feel free to ask any questions."
            self.chat_client.add_message_to_history(
                chat_uuid,
                {"role": "assistant", "content": assistant_message}
            )
            return {"type": "distillation", "status": "success", "content": session_distilled_md}

        except Exception as e:
            logging.error(f"Failed to process URL {url}: {e}", exc_info=True)
            return {"type": "error", "status": "failure", "content": f"Failed to process URL: {e}"}

    async def process_input(self, chat_uuid: str, user_input: str) -> dict:
        """
        Processes user input, routing to command handlers or the chat client.
        """
        if user_input.lower().startswith("/load "):
            url = user_input.split(" ", 1)[1]
            return await self._handle_load_command(chat_uuid, url, user_input)
        else:
            response = await self.chat_client.get_response(chat_uuid, user_input, self.model)
            return {"type": "chat", "content": response} 