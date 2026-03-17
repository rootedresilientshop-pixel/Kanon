from .intent import Intent, validate_with_context
from .observer import SafetyObserver
import json


class KanonSentry:
    def __init__(self, mode="autonomous", log_path="kanon_audit.log"):
        self.mode = mode
        self.observer = SafetyObserver(log_path)

    def check(self, intent: Intent, action: dict, state: dict = None):
        """
        The primary entry point for AI safety enforcement.
        """
        if state is None:
            state = {"values": {}}

        intent.mode = self.mode  # Sync mode with the Sentry instance

        try:
            return validate_with_context(intent, action, state)
        except ValueError as e:
            if self.mode == "certification":
                return self.observer.request_human_approval(
                    intent.id, action.get("params", {}), str(e)
                )
            # Re-raise for hard blocks
            raise e
