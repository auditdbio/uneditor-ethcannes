import dotenv
dotenv.load_dotenv()

from os import getenv
from enum import Enum

from uagents import Agent, Context, Model
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage

from chat_proto import chat_proto, struct_output_client_proto
from football import get_team_info, FootballTeamRequest, FootballTeamResponse

SEED_PHRASE = getenv("SEED_PHRASE")


agent = Agent(
    name="football_agent",
    seed=SEED_PHRASE,
    mailbox=True,
    port=8000,
    endpoint=["http://localhost:8000/submit"]
)

proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="Football-Team-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=30),
)

@proto.on_message(
    FootballTeamRequest, replies={FootballTeamResponse, ErrorMessage}
)
async def handle_request(ctx: Context, sender: str, msg: FootballTeamRequest):
    ctx.logger.info("Received team info request")
    try:
        results = await get_team_info(msg.team_name)
        ctx.logger.info(f'printing results in function {results}')
        ctx.logger.info("Successfully fetched team information")
        await ctx.send(sender, FootballTeamResponse(results=results))
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(sender, ErrorMessage(error=str(err)))

agent.include(proto, publish_manifest=True)

### Health check related code
def agent_is_healthy() -> bool:
    """
    Implement the actual health check logic here.
    For example, check if the agent can connect to the AllSports API.
    """
    try:
        import asyncio
        asyncio.run(get_team_info("Manchester United"))
        return True
    except Exception:
        return False

class HealthCheck(Model):
    pass

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class AgentHealth(Model):
    agent_name: str
    status: HealthStatus

health_protocol = QuotaProtocol(
    storage_reference=agent.storage, name="HealthProtocol", version="0.1.0"
)

@health_protocol.on_message(HealthCheck, replies={AgentHealth})
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    status = HealthStatus.UNHEALTHY
    try:
        if agent_is_healthy():
            status = HealthStatus.HEALTHY
    except Exception as err:
        ctx.logger.error(err)
    finally:
        await ctx.send(sender, AgentHealth(agent_name="football_agent", status=status))

agent.include(health_protocol, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)
agent.include(struct_output_client_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run() 