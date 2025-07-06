import os
import aiohttp
from datetime import datetime
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# --- Load Configuration ---
SEED_PHRASE = os.getenv("SEED_PHRASE")
AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL")
AGENT_API_SECRET_KEY = os.getenv("AGENT_API_SECRET_KEY")


# --- Initialize Agent ---
agent = Agent(name="science_chat_client", seed=SEED_PHRASE)

# --- Protocol Definition ---
chat_proto = Protocol(spec=chat_protocol_spec)

# --- Helper Function for API Calls ---
async def query_science_chat_api(chat_uuid: str, text: str, ctx: Context) -> str:
    """
    Queries the external FastAPI server for a response.
    """
    if not AGENT_SERVER_URL or not AGENT_API_SECRET_KEY:
        ctx.logger.error("AGENT_SERVER_URL or AGENT_API_SECRET_KEY not set!")
        return "Error: Client is not configured to connect to the backend service."

    api_url = f"{AGENT_SERVER_URL}/v1/chat/{chat_uuid}"
    headers = {"Authorization": f"Bearer {AGENT_API_SECRET_KEY}"}
    payload = {"text": text}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # For distillation, provide a summary message
                    if data.get("type") == "distillation":
                        return (f"Paper processed successfully. A distilled version is below.\n\n"
                                f"--- DISTILLED CONTENT ---\n{data['content']}")
                    # For standard chat, just return the content
                    return data.get("content", "Received an empty response.")
                else:
                    error_text = await response.text()
                    ctx.logger.error(f"API request failed with status {response.status}: {error_text}")
                    return f"Error: Failed to get response from backend (Status: {response.status})."
    except aiohttp.ClientError as e:
        ctx.logger.error(f"An HTTP error occurred: {e}")
        return "Error: Could not connect to the backend service."


# --- Message Handlers ---
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handles incoming messages from other agents, queries the backend, and replies.
    """
    for item in msg.content:
        if isinstance(item, TextContent):
            ctx.logger.info(f"Received message from {sender}: '{item.text}'")

            # Acknowledge receipt of the message
            ack = ChatAcknowledgement(acknowledged_msg_id=msg.msg_id, timestamp=datetime.utcnow())
            await ctx.send(sender, ack)
            
            # Use the sender's address as the unique chat ID
            chat_uuid = sender
            
            # Query the backend API and get the response
            backend_response = await query_science_chat_api(chat_uuid, item.text, ctx)

            # Send the backend's response back to the original sender
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=backend_response)]
            )
            await ctx.send(sender, response_msg)

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# --- Agent Inclusion ---
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    if not SEED_PHRASE or not AGENT_SERVER_URL or not AGENT_API_SECRET_KEY:
        print("ERROR: SEED_PHRASE, AGENT_SERVER_URL, and AGENT_API_SECRET_KEY must be set in the environment.")
    else:
        print(f"Agent address: {agent.address}")
        print(f"Connecting to backend at: {AGENT_SERVER_URL}")
        agent.run()