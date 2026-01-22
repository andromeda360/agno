from agno_v2.api.api import api
from agno_v2.api.routes import ApiRoutes
from agno_v2.api.schemas.agent import AgentRunCreate
from agno_v2.utils.log import log_debug


def create_agent_run(run: AgentRunCreate) -> None:
    """Telemetry recording for Agent runs"""
    with api.Client() as api_client:
        try:
            api_client.post(
                ApiRoutes.RUN_CREATE,
                json=run.model_dump(exclude_none=True),
            )
        except Exception as e:
            log_debug(f"Could not create Agent run: {e}")


async def acreate_agent_run(run: AgentRunCreate) -> None:
    """Telemetry recording for async Agent runs"""
    async with api.AsyncClient() as api_client:
        try:
            await api_client.post(
                ApiRoutes.RUN_CREATE,
                json=run.model_dump(exclude_none=True),
            )
        except Exception as e:
            log_debug(f"Could not create Agent run: {e}")
