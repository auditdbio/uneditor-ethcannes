import asyncio
import os
import uuid
from dotenv import load_dotenv
from models.chat import ChatClient

# ANSI escape codes for colors
USER_COLOR = "\033[94m"  # Blue
ASSISTANT_COLOR = "\033[92m"  # Green
SYSTEM_COLOR = "\033[93m" # Yellow
RESET_COLOR = "\033[0m"

def check_env_vars():
    """Checks if the required environment variables are set."""
    load_dotenv()
    required_vars = ["SAVANT_ROUTER_API_KEY", "VOYAGE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"{SYSTEM_COLOR}ERROR: Missing required environment variables: {', '.join(missing_vars)}{RESET_COLOR}")
        print(f"{SYSTEM_COLOR}Please add them to the models/.env file.{RESET_COLOR}")
        return False
    return True

async def run_console_chat():
    """
    Initializes and runs the interactive console chat interface.
    """
    if not check_env_vars():
        return

    model_name = "grok-3-mini-high"
    chat_client = ChatClient()
    chat_id = str(uuid.uuid4())

    print("---")
    print(f"{SYSTEM_COLOR}New Chat Session Started (ID: {chat_id}){RESET_COLOR}")
    print(f"{SYSTEM_COLOR}Using model: {model_name}{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}Type '/exit' or '/quit' to end the session.{RESET_COLOR}")
    print("---")

    while True:
        try:
            user_input = input(f"{USER_COLOR}You: {RESET_COLOR}").strip()
            
            if user_input.lower() in ["/exit", "/quit"]:
                print(f"{SYSTEM_COLOR}--- Chat session ended. ---{RESET_COLOR}")
                break
            
            if not user_input:
                continue

            # This is where we call the refactored ChatClient
            assistant_response = await chat_client.get_response(
                chat_uuid=chat_id,
                user_query=user_input,
                model=model_name
            )

            print(f"{ASSISTANT_COLOR}Assistant: {assistant_response}{RESET_COLOR}")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{SYSTEM_COLOR}--- Chat session ended. ---{RESET_COLOR}")
            break
        except Exception as e:
            print(f"{SYSTEM_COLOR}An error occurred: {e}{RESET_COLOR}")

if __name__ == "__main__":
    asyncio.run(run_console_chat()) 