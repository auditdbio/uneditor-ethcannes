from taskman import task, append_log
from models import chat_completions
from models.tools import exponential_backoff
from .. import TEMPLATES
import os
import lorem

@task(retries=8, retry_delay_seconds=exponential_backoff)
async def geography_expert_task() -> str:
    """Generates a description for a geographical object."""
    system_prompt = TEMPLATES.get_template("geography_expert_system.md").render()
    user_prompt = TEMPLATES.get_template("geography_expert_user.j2").render()

    await append_log(f"REQUEST:\n{system_prompt}\n{user_prompt}\n")

    if os.getenv("DRY_RUN") == "1":
        description = lorem.paragraph()
    else:
        description = await chat_completions(
            model="grok-3-mini-high",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5
        )

    await append_log(f"RESPONSE:\n{description}")

    return description 