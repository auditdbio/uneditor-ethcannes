import asyncio
import os
import uuid
from dotenv import load_dotenv

# It's important to load environment variables before importing the context manager
load_dotenv(dotenv_path='models/.env')

from models.models.context import ChatContextManager

async def main():
    """
    An example usage of the ChatContextManager to test its functionality.
    """
    print("--- Starting Chat Context Manager Test ---")

    # Ensure the API key is set
    if not os.getenv("VOYAGE_API_KEY"):
        print("\nERROR: VOYAGE_API_KEY is not set in models/.env")
        print("Please add your VoyageAI API key to the models/.env file and try again.")
        return

    context_manager = ChatContextManager()
    chat_id = str(uuid.uuid4())

    print(f"Created a new chat session with ID: {chat_id}")

    # 1. Simulate a conversation history and add it to the manager
    print("\n1. Simulating initial conversation...")
    initial_messages = [
        {
            "role": "user",
            "content": "What is the difference between supervised and unsupervised machine learning?"
        },
        {
            "role": "assistant",
            "content": "Supervised learning uses labeled data to train models, where the algorithm learns from input-output pairs. Unsupervised learning, on the other hand, works with unlabeled data to find hidden patterns or intrinsic structures in the dataset."
        },
        {
            "role": "user",
            "content": "Can you give an example of a supervised learning task?"
        },
        {
            "role": "assistant",
            "content": "Of course. A classic example is email spam detection. The model is trained on a large dataset of emails that are pre-labeled as 'spam' or 'not spam'. It learns to predict whether a new, unseen email is spam."
        }
    ]
    await context_manager.add_messages(chat_id, initial_messages)
    print("Added initial messages to the RAG context.")

    # 2. Define a new user query and the recent history to build the prompt from
    print("\n2. Simulating a new user query...")
    new_user_query = "What about an example for the other one?"
    
    # We pass the recent history to the prompt builder.
    # The full history has already been added to the RAG index.
    recent_chat_history = initial_messages + [{"role": "user", "content": new_user_query}]

    print(f"User Query: \"{new_user_query}\"")
    print(f"Recent History contains {len(recent_chat_history)} messages.")

    # 3. Build the prompt
    print("\n3. Building the final prompt...")
    system_prompt = await context_manager.build_system_prompt(
        chat_uuid=chat_id,
        user_query=new_user_query,
        chat_history=recent_chat_history,
        rag_top_k=2,
        max_context_chars=4000
    )

    # 4. Print the result
    print("\n--- GENERATED SYSTEM PROMPT (truncated to 4000 chars) ---")
    print(system_prompt)
    print("--------------------------------------------------")
    print("\n--- FINAL MESSAGE TO BE SENT TO API ---")
    print(f"System Prompt: [see above]")
    print(f"User Prompt: \"{new_user_query}\"")
    print("-----------------------------------------")
    print("\nTest finished. Check the prompt above to see how RAG context and dialogue history were combined.")


if __name__ == "__main__":
    asyncio.run(main()) 