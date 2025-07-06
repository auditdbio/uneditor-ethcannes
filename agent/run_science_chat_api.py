import asyncio
import os
import uuid
import aiohttp
from dotenv import load_dotenv

# --- Configuration and Colors ---
USER_COLOR = "\033[94m"
ASSISTANT_COLOR = "\033[92m"
SYSTEM_COLOR = "\033[93m"
ERROR_COLOR = "\033[91m"
RESET_COLOR = "\033[0m"

def load_and_check_env():
    """Loads environment variables and checks for required ones."""
    load_dotenv()
    
    api_url = os.getenv("API_BASE_URL")
    api_key = os.getenv("AGENT_API_SECRET_KEY")

    if not api_url or not api_key:
        print(f"{ERROR_COLOR}ERROR: API_BASE_URL and AGENT_API_SECRET_KEY must be set in agent/.env{RESET_COLOR}")
        return None, None
        
    return api_url, api_key

async def query_api(session, url, headers, payload):
    """A helper function to perform the API POST request."""
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            return {
                "type": "error",
                "content": f"API request failed with status {response.status}: {error_text}"
            }

async def main():
    """Initializes and runs the interactive API client."""
    api_base_url, api_key = load_and_check_env()
    if not api_base_url:
        return

    chat_id = str(uuid.uuid4())
    api_endpoint = f"{api_base_url}/v1/chat/{chat_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"\n{SYSTEM_COLOR}--- Science Chat API Client Initialized ---{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}Chat Session ID: {chat_id}{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}Target API: {api_base_url}{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}To load a paper, type: /load [URL_TO_PDF]{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}To exit, type: /exit or /quit{RESET_COLOR}")
    print(f"{SYSTEM_COLOR}-----------------------------------------{RESET_COLOR}")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                user_input = input(f"{USER_COLOR}You: {RESET_COLOR}").strip()

                if user_input.lower() in ["/exit", "/quit"]:
                    break
                if not user_input:
                    continue

                print(f"{SYSTEM_COLOR}Sending request...{RESET_COLOR}", end='\r')
                
                payload = {"text": user_input}
                result = await query_api(session, api_endpoint, headers, payload)
                
                print(" " * 20, end='\r')

                if result["type"] == "chat":
                    print(f"{ASSISTANT_COLOR}Assistant: {result['content']}{RESET_COLOR}")
                elif result["type"] == "distillation":
                    print(f"\n{SYSTEM_COLOR}--- DISTILLED PAPER ---{RESET_COLOR}")
                    print(result['content'])
                    print(f"{SYSTEM_COLOR}-----------------------{RESET_COLOR}")
                    print(f"{ASSISTANT_COLOR}Assistant: I have finished processing the paper. Both versions are in context. Ask me anything.{RESET_COLOR}")
                elif result["type"] == "error":
                    print(f"{ERROR_COLOR}Error: {result['content']}{RESET_COLOR}")

            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"{ERROR_COLOR}\nAn unexpected client error occurred: {e}{RESET_COLOR}")

    print(f"\n{SYSTEM_COLOR}--- Chat session ended. ---{RESET_COLOR}")

if __name__ == "__main__":
    asyncio.run(main()) 