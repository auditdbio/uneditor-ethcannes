from taskman import task, append_log
from models import chat_completions
from models.tools import exponential_backoff, parse_json_from_text
from .. import TEMPLATES
import json
import random
import os

@task(retries=8, retry_delay_seconds=exponential_backoff, cache_on=("object_name",))
async def world_classifier_task(object_name: str) -> str:
    """Classifies a geographical object as 'old' or 'new' world."""
    system_prompt = TEMPLATES.get_template("world_classifier_system.md").render()
    user_prompt = TEMPLATES.get_template("world_classifier_user.j2").render(object_name=object_name)

    await append_log(f"REQUEST:\n{system_prompt}\n{user_prompt}\n")

    if os.getenv("DRY_RUN") == "1":
        world_choice = random.choice(["old", "new"])
        response = json.dumps({"world": world_choice})
    else:
        response = await chat_completions(
            model="grok-3-mini-high",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5
        )
    
    await append_log(f"RESPONSE:\n{response}")

    try:
        data = parse_json_from_text(response)
        return data.get("world", "unknown")
    except (ValueError, AttributeError):
        return "unknown" 