# 🚀 uneditor: Your GPS for Scientific Knowledge 🛰️

> "This is the paper that cited the student that referenced the professor that analyzed the data for the theory that underpins the model that Jack built." 

Tired of navigating the recursive labyrinth of academic papers? Traditional science is a magnificent, sprawling mansion, but for engineers in fast-moving fields like AI and Blockchain, it often feels like "The House That Jack Built" — a winding narrative full of historical detours, social pleasantries, and endless citations.

We don't need a lengthy poem. We need an **electronic map with a GPS navigator**. 🗺️

**uneditor** is that navigator. It's an AI agent designed to accelerate R&D by distilling dense scientific papers into their core intellectual essence. It surgically removes the academic "social glue" — literature reviews, acknowledgements, and roundabout references — to give you the signal without the noise.

## ✨ The Mission: Straight to the "Aha!" Moment

The core purpose of `uneditor` is to transform a paper into a lucid technical monograph. It helps engineers and researchers quickly grasp the central claim, the core mechanism, and the hard evidence, enabling them to build, critique, and innovate faster.

The agent's philosophy is guided by the [`unredactor.j2`](./agent/agent/prompts/unredactor.j2) prompt: distill, don't just summarize.

## 🤖 Try it Live!

You can interact with the agent here:
[**uneditor on agentverse.ai**](https://agentverse.ai/agents/details/agent1qvw8wggsdmcrx6et9jgkezasudga5amsvr5ay5ffyskhsl8fdzypsd2mdlt/profile)

## 🛠️ How it Works

1.  **Load & Distill:** Simply use the command `/load <url>` with a link to a scientific paper (e.g., a PDF on arXiv).
2.  **Discuss & Explore:** The agent will provide a distilled version. You can then ask questions, discuss the concepts, and even load more papers into the context to compare and contrast ideas.

## 💻 Tech Stack

`uneditor` is built on a modern stack for efficient document processing and analysis:

*   **PDF Conversion:** `marker` for robust PDF-to-Markdown conversion.
*   **RAG Pipeline:**
    *   `voyageai` for high-quality embeddings and reranking.
    *   `langchain` for intelligent document chunking.
    *   `faiss` for lightning-fast similarity search.
*   **LLM Core:**
    *   `grok-3-mini`: For budget-friendly, high-speed inference (perfect for hackathons! 🏆).
    *   `gemini-2.5-pro`: For production-grade, in-depth analysis.

---

Let's accelerate science and build the future, faster. ⏩