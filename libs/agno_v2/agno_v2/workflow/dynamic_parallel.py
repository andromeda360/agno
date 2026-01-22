"""
DynamicParallel - Parallel step execution with runtime-generated steps.

Extends Agno's Parallel construct to generate steps dynamically based on
runtime data (e.g., pool definitions from a previous step).
"""

import logging
from typing import Any, AsyncIterator, Callable, Dict, Iterator, List, Optional, Union

from agno_v2.run.agent import RunOutputEvent
from agno_v2.run.team import TeamRunOutputEvent
from agno_v2.run.workflow import WorkflowRunOutput, WorkflowRunOutputEvent
from agno_v2.workflow.parallel import Parallel
from agno_v2.workflow.step import Step
from agno_v2.workflow.types import StepInput, StepOutput

logger = logging.getLogger(__name__)


class DynamicParallel(Parallel):
    """
    Parallel that generates steps dynamically from runtime data.

    Unlike the standard Parallel which requires steps to be defined at init time,
    DynamicParallel uses a step_generator function that creates steps based on
    the previous step's output at execution time.

    Example:
        def create_fetch_steps(step_input: StepInput) -> List[Step]:
            pools = step_input.previous_step_content
            return [
                Step(name=f"Fetch_{p['name']}", executor=FetchPool(p))
                for p in pools
            ]

        DynamicParallel(
            step_generator=create_fetch_steps,
            name="FetchAllPools"
        )
    """

    def __init__(
        self,
        step_generator: Callable[[StepInput], List[Step]],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize DynamicParallel.

        Args:
            step_generator: Function that takes StepInput and returns List[Step].
                           Called at execution time to generate steps dynamically.
            name: Optional name for the parallel step.
            description: Optional description.
        """
        # Initialize with empty steps - we'll generate them at runtime
        self.step_generator = step_generator
        self.name = name
        self.description = description
        self.steps = []  # Will be populated by _generate_steps

    def _generate_steps(self, step_input: StepInput) -> None:
        """
        Generate steps from the step_generator function.

        Called before each execute method to dynamically create steps
        based on the previous step's output.
        """
        try:
            generated_steps = self.step_generator(step_input)
            if not isinstance(generated_steps, list):
                logger.error(f"step_generator must return a list, got {type(generated_steps)}")
                self.steps = []
            else:
                self.steps = generated_steps
                logger.info(f"DynamicParallel '{self.name}' generated {len(self.steps)} steps")
        except Exception as e:
            logger.error(f"DynamicParallel step generation failed: {e}")
            self.steps = []

    def execute(
        self,
        step_input: StepInput,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        workflow_run_response: Optional[WorkflowRunOutput] = None,
        store_executor_outputs: bool = True,
        session_state: Optional[Dict[str, Any]] = None,
        **kwargs,  # Forward any additional args to parent
    ) -> StepOutput:
        """Execute all dynamically generated steps in parallel."""
        self._generate_steps(step_input)

        if not self.steps:
            logger.warning(f"DynamicParallel '{self.name}' has no steps to execute")
            return StepOutput(
                step_name=self.name or "DynamicParallel",
                step_type="Parallel",
                content="No steps generated",
                success=True,
                steps=[],
            )

        return super().execute(
            step_input,
            session_id=session_id,
            user_id=user_id,
            workflow_run_response=workflow_run_response,
            store_executor_outputs=store_executor_outputs,
            session_state=session_state,
            **kwargs,
        )

    async def aexecute(
        self,
        step_input: StepInput,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        workflow_run_response: Optional[WorkflowRunOutput] = None,
        store_executor_outputs: bool = True,
        session_state: Optional[Dict[str, Any]] = None,
        **kwargs,  # Forward any additional args to parent
    ) -> StepOutput:
        """Execute all dynamically generated steps in parallel (async)."""
        self._generate_steps(step_input)

        if not self.steps:
            logger.warning(f"DynamicParallel '{self.name}' has no steps to execute")
            return StepOutput(
                step_name=self.name or "DynamicParallel",
                step_type="Parallel",
                content="No steps generated",
                success=True,
                steps=[],
            )

        return await super().aexecute(
            step_input,
            session_id=session_id,
            user_id=user_id,
            workflow_run_response=workflow_run_response,
            store_executor_outputs=store_executor_outputs,
            session_state=session_state,
            **kwargs,
        )

    def execute_stream(
        self,
        step_input: StepInput,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        stream_intermediate_steps: bool = False,
        workflow_run_response: Optional[WorkflowRunOutput] = None,
        step_index: Optional[Union[int, tuple]] = None,
        store_executor_outputs: bool = True,
        session_state: Optional[Dict[str, Any]] = None,
        parent_step_id: Optional[str] = None,
        **kwargs,  # Forward any additional args to parent
    ) -> Iterator[Union[WorkflowRunOutputEvent, StepOutput]]:
        """Execute all dynamically generated steps in parallel with streaming."""
        self._generate_steps(step_input)

        if not self.steps:
            logger.warning(f"DynamicParallel '{self.name}' has no steps to execute")
            yield StepOutput(
                step_name=self.name or "DynamicParallel",
                step_type="Parallel",
                content="No steps generated",
                success=True,
                steps=[],
            )
            return

        yield from super().execute_stream(
            step_input,
            session_id=session_id,
            user_id=user_id,
            stream_intermediate_steps=stream_intermediate_steps,
            workflow_run_response=workflow_run_response,
            step_index=step_index,
            store_executor_outputs=store_executor_outputs,
            session_state=session_state,
            parent_step_id=parent_step_id,
            **kwargs,
        )

    async def aexecute_stream(
        self,
        step_input: StepInput,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        stream_intermediate_steps: bool = False,
        workflow_run_response: Optional[WorkflowRunOutput] = None,
        step_index: Optional[Union[int, tuple]] = None,
        store_executor_outputs: bool = True,
        session_state: Optional[Dict[str, Any]] = None,
        parent_step_id: Optional[str] = None,
        **kwargs,  # Forward any additional args to parent
    ) -> AsyncIterator[Union[WorkflowRunOutputEvent, TeamRunOutputEvent, RunOutputEvent, StepOutput]]:
        """Execute all dynamically generated steps in parallel with async streaming."""
        self._generate_steps(step_input)

        if not self.steps:
            logger.warning(f"DynamicParallel '{self.name}' has no steps to execute")
            yield StepOutput(
                step_name=self.name or "DynamicParallel",
                step_type="Parallel",
                content="No steps generated",
                success=True,
                steps=[],
            )
            return

        async for event in super().aexecute_stream(
            step_input,
            session_id=session_id,
            user_id=user_id,
            stream_intermediate_steps=stream_intermediate_steps,
            workflow_run_response=workflow_run_response,
            step_index=step_index,
            store_executor_outputs=store_executor_outputs,
            session_state=session_state,
            parent_step_id=parent_step_id,
            **kwargs,
        ):
            yield event
