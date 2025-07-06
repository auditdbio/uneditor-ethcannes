import asyncio
import uuid
from typing import List, Dict

from .context import ChatContextManager
from . import chat_completions

class ChatClient:
    """
    A low-level client that manages multiple chat sessions, generates contexts,
    and interacts with the language model. It does not handle UI.
    """
    def __init__(self):
        self.context_manager = ChatContextManager()
        self.chat_histories: Dict[str, List[Dict[str, str]]] = {}

    def _get_or_create_history(self, chat_uuid: str) -> List[Dict[str, str]]:
        """Retrieves or creates the chat history for a given UUID."""
        if chat_uuid not in self.chat_histories:
            self.chat_histories[chat_uuid] = []
        return self.chat_histories[chat_uuid]

    def add_message_to_history(self, chat_uuid: str, message: Dict[str, str]):
        """Adds a message to the chat history without generating a response."""
        history = self._get_or_create_history(chat_uuid)
        history.append(message)

    async def get_response(self, chat_uuid: str, user_query: str, model: str) -> str:
        """
        Handles a single user query, gets a model response, and updates history.
        """
        history = self._get_or_create_history(chat_uuid)
        history.append({"role": "user", "content": user_query})

        system_prompt = await self.context_manager.build_system_prompt(
            chat_uuid=chat_uuid,
            user_query=user_query,
            chat_history=history,
            rag_top_k=3
        )

        assistant_response = await chat_completions(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_query
        )

        history.append({"role": "assistant", "content": assistant_response})
        
        # Add the latest exchange to the RAG index for future reference
        await self.context_manager.add_messages(
            chat_uuid,
            [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_response},
            ]
        )
        return assistant_response

    async def add_document(self, chat_uuid: str, document_content: str):
        """
        Adds a document to the RAG context of a specific chat session
        without generating a response.
        """
        # We add the document with a 'system' role to distinguish it in the RAG store
        await self.context_manager.add_messages(
            chat_uuid,
            [{"role": "system", "content": f"Reference document:\n{document_content}"}]
        ) 