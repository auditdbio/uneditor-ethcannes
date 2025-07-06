import asyncio
import os
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from agent.science_chat import ScienceChatOrchestrator
from models.chat import ChatClient

# ANSI escape codes for colors
USER_COLOR = "\033[94m"
ASSISTANT_COLOR = "\033[92m"
SYSTEM_COLOR = "\033[93m"
ERROR_COLOR = "\033[91m"
RESET_COLOR = "\033[0m"

def check_env_vars():
    """Checks if the required environment variables are set."""
    load_dotenv(dotenv_path='models/.env')
    required_vars = ["SAVANT_ROUTER_API_KEY", "VOYAGE_API_KEY", "DATALAB_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"{ERROR_COLOR}ERROR: Missing required environment variables: {', '.join(missing_vars)}{RESET_COLOR}")
        print(f"{SYSTEM_COLOR}Please add them to the models/.env file.{RESET_COLOR}")
        return False
    return True

async def main():
    """Initializes and runs the interactive science chat."""
    if not check_env_vars():
        return

    chat_client = ChatClient()
    orchestrator = ScienceChatOrchestrator(chat_client=chat_client, model_name="grok-3-mini-high")

    print(f"\n{SYSTEM_COLOR}--- Science Chat Initialized ---{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}Using model: {orchestrator.model}{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}To load a paper, type: /load [URL_TO_PDF]{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}To exit, type: /exit or /quit{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}----------------------------------{RESET_COLOR}")

    history = InMemoryHistory()
    session = PromptSession(history=history)

    while True:
        try:
            # Use prompt_toolkit's styling for the prompt, as raw ANSI codes can cause rendering issues.
            user_input = (await session.prompt_async([('fg:ansibrightblue', 'You: ')])).strip()

            if user_input.lower() in ["/exit", "/quit"]:
                print(f"{SYSTEM_COLOR}--- Chat session ended. ---{RESET_COLOR}")
                break
            if not user_input:
                continue

            print(f"{SYSTEM_COLOR}Processing...{RESET_COLOR}", end='\r')
            result = await orchestrator.process_input("console_chat", user_input)
            print(" " * 20, end='\r') # Clear the "Processing..." message

            if result["type"] == "chat":
                print(f"{ASSISTANT_COLOR}Assistant: {result['content']}{RESET_COLOR}")

            elif result["type"] == "distillation":
                print(f"\n{SYSTEM_COLOR}--- DISTILLED PAPER ---{RESET_COLOR}")
                print(result['content'])
                print(f"{SYSTEM_COLOR}-----------------------{RESET_COLOR}")
                print(f"{ASSISTANT_COLOR}Assistant: I have finished processing the paper. Both the original and the distilled versions are now in my context. Feel free to ask any questions.{RESET_COLOR}")
            
            elif result["type"] == "error":
                print(f"{ERROR_COLOR}Error: {result['content']}{RESET_COLOR}")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{SYSTEM_COLOR}--- Chat session ended. ---{RESET_COLOR}")
            break
        except Exception as e:
            print(f"{ERROR_COLOR}An unexpected application error occurred: {e}{RESET_COLOR}")

if __name__ == "__main__":
    asyncio.run(main()) 