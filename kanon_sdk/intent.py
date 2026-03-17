from typing import List, Union, Literal
from pydantic import BaseModel, Field


class Constraint(BaseModel):
    """A deterministic boundary for an action."""

    attribute: str
    operator: Literal["<", ">", "==", "<=", ">=", "in", "not_in"]
    value: Union[int, float, str, List[str]]
    priority: int = Field(
        default=1,
        description="Higher priority constraints are enforced first.",
    )


class Objective(BaseModel):
    """The high-level goal the agent is pursuing."""

    name: str
    target: Literal["maximize", "minimize", "maintain"]
    metric: str


class Intent(BaseModel):
    """The root container for a Kanon 'Mission'."""

    id: str
    version: str = "0.1.0"
    objective: Objective
    constraints: List[Constraint]
    mode: Literal["creative", "certification"] = "creative"

    def to_json(self):
        return self.model_dump_json()


def validate_with_context(intent: Intent, action_dict: dict, state_dict: dict):
    import json
    from kanon_sdk import kanon_core

    return kanon_core.validate_intent_json(
        intent.to_json(),
        json.dumps(action_dict),
        json.dumps(state_dict),
    )
