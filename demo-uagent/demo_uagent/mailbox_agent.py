from dotenv import load_dotenv
load_dotenv()

from os import getenv

from uagents import Agent, Context, Model
 
class Message(Model):
    message: str
 
SEED_PHRASE = getenv("SEED_PHRASE")
 
# Now your agent is ready to join the Agentverse!
agent = Agent(
    name="alice",
    port=8000,
    mailbox=True,
    seed=SEED_PHRASE        
)
 
# Copy the address shown below
print(f"Your agent's address is: {agent.address}")
 
if __name__ == "__main__":
    agent.run()