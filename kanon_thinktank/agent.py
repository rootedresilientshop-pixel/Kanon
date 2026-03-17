from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from kanon_sdk import kanon_core
from kanon_sdk.intent import Constraint, Intent, Objective


class KanonAgent:
    def __init__(self, name: str, mode: str = "creative") -> None:
        self.name = name
        self.mode = mode

    def propose_action(
        self,
        raw_suggestion: str,
        intent_id: str,
        constraints: List[Constraint] | None = None,
        objective: Objective | None = None,
    ) -> Tuple[Intent, Dict[str, Any]]:
        if objective is None:
            objective = Objective(name=raw_suggestion, target="maintain", metric="safety")
        if constraints is None:
            constraints = []

        intent = Intent(
            id=intent_id,
            objective=objective,
            constraints=constraints,
            mode=self.mode,
        )

        action = {"params": {"suggestion": raw_suggestion, "agent": self.name}}
        return intent, action

    def validate_action(self, intent: Intent, action: Dict[str, Any], state: Dict[str, Any]) -> bool:
        try:
            return bool(
                kanon_core.validate_intent_json(
                    intent.to_json(),
                    json.dumps(action),
                    json.dumps(state),
                )
            )
        except Exception:
            return False