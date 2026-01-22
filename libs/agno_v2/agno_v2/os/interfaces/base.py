from abc import ABC, abstractmethod
from typing import List, Optional

from fastapi import APIRouter

from agno_v2.agent import Agent
from agno_v2.team import Team
from agno_v2.workflow.workflow import Workflow


class BaseInterface(ABC):
    type: str
    version: str = "1.0"
    agent: Optional[Agent] = None
    team: Optional[Team] = None
    workflow: Optional[Workflow] = None

    prefix: str
    tags: List[str]

    router: APIRouter

    @abstractmethod
    def get_router(self, use_async: bool = True, **kwargs) -> APIRouter:
        pass
