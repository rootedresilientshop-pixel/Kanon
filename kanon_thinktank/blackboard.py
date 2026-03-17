from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import Any, Dict

from pydantic import BaseModel, Field


class BlackboardEntry(BaseModel):
    audit_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    payload: Dict[str, Any]


class BlackboardState(BaseModel):
    context: Dict[str, BlackboardEntry]


class Blackboard:
    def __init__(self) -> None:
        self._lock = RLock()
        self._context: "OrderedDict[str, BlackboardEntry]" = OrderedDict()

    def post_intent(self, key: str, intent_payload: Dict[str, Any], audit_id: str) -> None:
        entry = BlackboardEntry(audit_id=audit_id, kind="intent", payload=intent_payload)
        with self._lock:
            self._context[key] = entry

    def commit_action(self, key: str, action_payload: Dict[str, Any], audit_id: str) -> None:
        entry = BlackboardEntry(audit_id=audit_id, kind="action", payload=action_payload)
        with self._lock:
            self._context[key] = entry

    def get_state(self) -> BlackboardState:
        with self._lock:
            snapshot: Dict[str, BlackboardEntry] = dict(self._context)
        return BlackboardState(context=snapshot)