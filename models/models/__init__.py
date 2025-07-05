from openai import AsyncOpenAI, NOT_GIVEN
from typing import Optional, List, Dict, Any
import aiohttp
from os import getenv

from .semaphore import RLSemaphore

# --- Model-specific Semaphores ---
_SEMAPHORES: Dict[str, RLSemaphore] = {}

def get_semaphore(model: str) -> RLSemaphore:
    """Creates and retrieves a semaphore for a specific model to manage concurrency."""
    if model not in _SEMAPHORES:
        _SEMAPHORES[model] = RLSemaphore() # Parameters are now fetched inside
    return _SEMAPHORES[model]

# --- API Functions ---

async def chat_completions(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float] = None,
) -> str:
    """Get chat completions from the OpenAI-compatible API."""
    async with get_semaphore(model):
        api_key = getenv("SAVANT_ROUTER_API_KEY")
        request_timeout = int(getenv("REQUEST_TIMEOUT", "1800"))
        task_id = getenv("TASK_ID", None)
        
        client = AsyncOpenAI(api_key=api_key, base_url="https://router.savant.chat/api")
        
        extra_body = {"task_name": task_id} if task_id else {}

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature if temperature is not None else NOT_GIVEN,
            extra_body=extra_body,
            timeout=request_timeout
        )
        return response.choices[0].message.content.strip()

async def embeddings(model: str, texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts from the VoyageAI API."""
    async with get_semaphore(model):
        api_key = getenv("VOYAGE_API_KEY")
        request_timeout = int(getenv("REQUEST_TIMEOUT", "1800"))

        client = AsyncOpenAI(api_key=api_key, base_url="https://api.voyageai.com/v1")
        response = await client.embeddings.create(
            model=model,
            input=texts,
            timeout=request_timeout
        )
        return [item.embedding for item in response.data]

async def rerank(
    model: str,
    query: str,
    documents: List[str],
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """Rerank documents based on a query using the VoyageAI API."""
    async with get_semaphore(model):
        api_key = getenv("VOYAGE_API_KEY")
        request_timeout = int(getenv("REQUEST_TIMEOUT", "1800"))

        async with aiohttp.ClientSession() as session:
            payload = {
                "query": query,
                "documents": documents,
                "model": model,
                "top_k": top_k,
                "return_documents": False,
                "truncation": True,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            async with session.post("https://api.voyageai.com/v1/rerank", headers=headers, json=payload, timeout=request_timeout) as response:
                return await response.json() 