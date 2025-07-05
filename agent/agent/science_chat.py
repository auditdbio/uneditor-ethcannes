import asyncio
import pathlib
import uuid
import aiohttp
import aiofiles
import jinja2
from models.chat import ChatClient
from models.datalab import process_pdf_with_datalab
from models import chat_completions

class ScienceChatOrchestrator:
    """
    Orchestrates the lifecycle of a scientific chat session. Handles commands,
    document processing (download, parsing, distillation), and regular chat.
    """
    def __init__(self, model_name: str = "grok-3-mini-high"):
        self.chat_client = ChatClient()
        self.chat_uuid = str(uuid.uuid4())
        self.model = model_name
        self.distillation_model = "grok-3-mini-high" # Use a powerful model for distillation
        self._load_unredactor_prompt()
        self.download_dir = pathlib.Path("temp_downloads")
        self.download_dir.mkdir(exist_ok=True)

    def _load_unredactor_prompt(self):
        """Loads the distillation prompt template from the file."""
        template_dir = pathlib.Path(__file__).parent / "prompts"
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        self.unredactor_template = env.get_template("unredactor.j2")

    async def _download_pdf(self, url: str) -> pathlib.Path:
        """Downloads a PDF from a URL to a temporary directory."""
        filename = self.download_dir / f"{self.chat_uuid}_{url.split('/')[-1]}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                async with aiofiles.open(filename, 'wb') as f:
                    await f.write(await response.read())
        return filename

    async def _distill_text(self, paper_content: str) -> str:
        """Generates a distilled version of the paper using an LLM."""
        user_prompt = self.unredactor_template.render(paper=paper_content)
        system_prompt = "You are a Master Educator and Technical Author. Your task is to take a dense, raw academic paper and transform it into a lucid, self-contained technical monograph."
        
        distilled_content = await chat_completions(
            model=self.distillation_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        return distilled_content

    async def _handle_load_command(self, url: str) -> dict:
        """Orchestrates the full PDF processing pipeline."""
        try:
            # 1. Download
            pdf_path = await self._download_pdf(url)
            
            # 2. Parse with Datalab
            output_dir = self.download_dir / f"output_{pdf_path.stem}"
            raw_markdown = await process_pdf_with_datalab(pdf_path, output_dir)
            if not raw_markdown:
                raise ValueError("Failed to parse PDF with Datalab.")

            # 3. Distill
            distilled_markdown = await self._distill_text(raw_markdown)

            # 4. Add both versions to RAG context
            await self.chat_client.add_document(self.chat_uuid, raw_markdown)
            await self.chat_client.add_document(self.chat_uuid, distilled_markdown)

            # 5. Return distilled text for display
            return {"type": "distillation", "status": "success", "content": distilled_markdown}

        except Exception as e:
            return {"type": "error", "status": "failure", "content": f"Failed to process URL: {e}"}

    async def process_input(self, user_input: str) -> dict:
        """
        Processes user input, routing to command handlers or the chat client.
        """
        if user_input.lower().startswith("/load "):
            url = user_input.split(" ", 1)[1]
            return await self._handle_load_command(url)
        else:
            response = await self.chat_client.get_response(self.chat_uuid, user_input, self.model)
            return {"type": "chat", "content": response} 