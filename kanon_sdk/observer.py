import json
import time
from pathlib import Path


class SafetyObserver:
    def __init__(self, log_path: str = "kanon_audit.log"):
        self.log_path = Path(log_path)

    def request_human_approval(self, intent_id: str, action_params: dict, reason: str) -> bool:
        """A simple CLI-based approval system for human-in-the-loop flow."""
        print("\n" + "!" * 30)
        print("SAFETY INTERVENTION REQUIRED")
        print(f"Intent: {intent_id}")
        print(f"Action: {json.dumps(action_params, indent=2)}")
        print(f"Violation: {reason}")
        print("!" * 30)

        choice = input("Authorize this override? (y/N): ").lower()
        return choice == "y"

    def monitor(self):
        """Tail the log file for new entries (simplified placeholder)."""
        print("Kanon Observer is live. Watching for interventions...")
        time.sleep(0.1)
