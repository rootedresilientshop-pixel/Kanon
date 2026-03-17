from __future__ import annotations

from typing import Dict, Iterable, Optional
from uuid import uuid4

from kanon_sdk.observer import SafetyObserver

from .agent import KanonAgent
from .blackboard import Blackboard


def _model_to_dict(model) -> Dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


class Orchestrator:
    def __init__(
        self,
        blackboard: Blackboard,
        agents: Iterable[KanonAgent],
        mode: str = "creative",
        observer: Optional[SafetyObserver] = None,
    ) -> None:
        self.blackboard = blackboard
        self.agents = list(agents)
        self.mode = mode
        self.observer = observer or SafetyObserver()

    def run_once(self, suggestions: Dict[str, str]) -> None:
        state_model = self.blackboard.get_state()
        state = _model_to_dict(state_model)

        for agent in self.agents:
            if agent.name not in suggestions:
                continue

            raw = suggestions[agent.name]
            intent, action = agent.propose_action(
                raw_suggestion=raw,
                intent_id=f"{agent.name}-{uuid4().hex}",
            )

            if self.mode == "certification":
                approved = self.observer.request_human_approval(
                    intent.id, action.get("params", {}), "Certification required"
                )
                if not approved:
                    continue

            is_valid = agent.validate_action(intent, action, state)
            audit_id = uuid4().hex

            if is_valid:
                self.blackboard.post_intent(intent.id, intent.model_dump(), audit_id)
                self.blackboard.commit_action(intent.id, action, audit_id)
            else:
                self.observer.request_human_approval(
                    intent.id, action.get("params", {}), "Validation failed"
                )