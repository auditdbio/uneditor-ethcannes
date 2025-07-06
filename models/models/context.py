import asyncio
import logging
from typing import List, Dict, Optional, Any

import faiss
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter

from . import embeddings, rerank

# --- Constants ---
EMBEDDING_DIM = 1024  # As per VoyageAI documentation for voyage-3 model
RAG_CHUNK_SIZE = 4096    # Characters
RAG_CHUNK_OVERLAP = 256  # Characters

class ChatSession:
    """
    Manages the context for a single, isolated chat session.
    This includes an in-memory FAISS index for RAG.
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP,
            length_function=len,
        )
        # The FAISS index for vector search
        self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
        # A simple list to store the actual text chunks corresponding to the vectors
        self.chunk_store: List[str] = []

    async def add_text(self, text: str):
        """
        Splits text into chunks, creates embeddings, and adds them to the FAISS index.
        """
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            logging.warning(f"Text splitting resulted in 0 chunks for a text of length {len(text)}. Not adding to RAG index.")
            return

        embedding_vectors = await embeddings(model="voyage-3", texts=chunks)
        self.index.add(np.array(embedding_vectors, dtype="float32"))
        self.chunk_store.extend(chunks)
        logging.info(f"Added {len(chunks)} chunks to the RAG index. Total chunks in store: {self.index.ntotal}")

    async def retrieve_rag_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieves the most relevant text chunks from the session's history using RAG.
        """
        if self.index.ntotal == 0:
            return ""

        query_embedding_list = await embeddings(model="voyage-3", texts=[query])
        query_embedding = np.array(query_embedding_list, dtype="float32")

        # --- Defensive check to prevent FAISS segfault ---
        if query_embedding.ndim != 2 or query_embedding.shape[1] != self.index.d:
            logging.error(
                f"CRITICAL: Embedding dimension mismatch! Index dimension is {self.index.d}, "
                f"but query vector dimension is {query_embedding.shape[1]}. "
                f"Please check the 'EMBEDDING_DIM' constant in context.py against the 'voyage-3' model's output."
            )
            # Return empty context instead of crashing the server
            return ""
        # --- End of defensive check ---

        # Search more candidates to give the reranker a better selection
        search_k = min(top_k * 5, self.index.ntotal)
        logging.info(f"FAISS search: Performing search for {search_k} nearest neighbors.")
        _, indices = self.index.search(query_embedding, k=search_k)
        
        candidate_docs = [self.chunk_store[i] for i in indices[0]]
        logging.info(f"FAISS search: Found {len(candidate_docs)} initial candidates.")

        if not candidate_docs:
            return ""

        # If we have fewer candidates than top_k, no need to rerank.
        if len(candidate_docs) <= top_k:
            logging.info(f"Skipping reranker as the number of candidates ({len(candidate_docs)}) is not greater than top_k ({top_k}).")
            return "\n\n".join(candidate_docs)

        # Rerank the documents to improve relevance
        logging.info(f"Reranking: Sending {len(candidate_docs)} candidates to the reranker.")
        rerank_response = await rerank(
            model="rerank-2",
            query=query,
            documents=candidate_docs,
            top_k=top_k,
        )
        
        # The reranker API returns documents in the 'data' field, with an 'index'
        # pointing to the original candidate_docs list.
        reranked_results = rerank_response.get("data", [])
        final_docs = [candidate_docs[result["index"]] for result in reranked_results]
        logging.info(f"Reranking: Received {len(final_docs)} documents after reranking.")

        return "\n\n".join(final_docs)


class ChatContextManager:
    """
    Manages multiple ChatSession instances, each identified by a unique chat_uuid.
    Provides a high-level interface to build the final prompt context.
    """
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def _get_or_create_session(self, chat_uuid: str) -> ChatSession:
        """
        Retrieves an existing session or creates a new one if it doesn't exist.
        """
        if chat_uuid not in self.sessions:
            self.sessions[chat_uuid] = ChatSession()
        return self.sessions[chat_uuid]

    async def add_messages(self, chat_uuid: str, messages: List[Dict[str, str]]):
        """
        Adds a list of messages to the specified chat's RAG context.
        """
        session = self._get_or_create_session(chat_uuid)
        # Process all messages concurrently for efficiency
        tasks = []
        for message in messages:
            text_to_add = f"{message.get('role', 'user')}: {message.get('content', '')}"
            tasks.append(session.add_text(text_to_add))
        await asyncio.gather(*tasks)

    async def add_document(self, chat_uuid: str, document_content: str):
        """
        Adds raw document content to the specified chat's RAG context.
        """
        session = self._get_or_create_session(chat_uuid)
        await session.add_text(document_content)

    async def build_system_prompt(
        self,
        chat_uuid: str,
        user_query: str,
        chat_history: List[Dict[str, str]],
        rag_top_k: int = 3,
        max_context_chars: int = 128000,
    ) -> str:
        """
        Builds the final system prompt by combining RAG context and chat history.
        Ensures the total length does not exceed the specified maximum.
        """
        session = self._get_or_create_session(chat_uuid)

        # 1. Retrieve RAG context
        rag_context = await session.retrieve_rag_context(user_query, top_k=rag_top_k)

        # 2. Format chat history
        history_str = "\n".join(
            [f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in chat_history]
        )

        # 3. Assemble the prompt template
        prompt_template = """You are an expert AI assistant.
Use the following context from previous discussions and documents to answer the user's question.
If the context is not relevant, ignore it and rely on the dialogue history.

--- RELEVANT CONTEXT (RAG) ---
{rag_context}
------------------------------

--- DIALOGUE HISTORY ---
{chat_history}
----------------------
"""

        # 4. Fill the template and manage length
        base_prompt_len = len(prompt_template.format(rag_context="", chat_history=""))
        remaining_space = max_context_chars - base_prompt_len

        # Prioritize chat history, then RAG context
        if len(history_str) > remaining_space:
            history_str = history_str[-remaining_space:] # Truncate from the beginning
            rag_context = "" # No space left for RAG
        else:
            rag_space = remaining_space - len(history_str)
            if len(rag_context) > rag_space:
                rag_context = rag_context[:rag_space] # Truncate RAG context
        
        return prompt_template.format(
            rag_context=rag_context,
            chat_history=history_str
        ) 