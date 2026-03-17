import json
import os
from kanon_sdk.intent import Intent, Objective, Constraint
from kanon_sdk import kanon_core
from kanon_sdk.observer import SafetyObserver

observer = SafetyObserver()

os.environ.setdefault(
    "KANON_SEED",
    "52a113c7082ed9449f205b81336afe1071cd49bce205d68a3e976014aaf02d5c",
)


def execute_action(intent, action_dict):
    action_json = json.dumps(action_dict)
    state_json = json.dumps({"values": {}})
    try:
        kanon_core.validate_intent_json(intent.to_json(), action_json, state_json)
        print("Action executed.")
    except ValueError as e:
        if intent.mode == "certification":
            if observer.request_human_approval(intent.id, action_dict["params"], str(e)):
                print("MANUAL OVERRIDE: Action executed by human authority.")
            else:
                print("ACTION ABORTED: Human denied override.")
        else:
            print(f"CRITICAL BLOCK: {e}")


# 1. Define the 'Safety Polygon' (The Rules)
intent = Intent(
    id="mkt-001",
    objective=Objective(name="Spend", target="minimize", metric="cost"),
    constraints=[
        Constraint(attribute="daily_budget", operator="<=", value=100.0)
    ]
)

# Test Certification Mode
intent.mode = "certification"
execute_action(intent, {"params": {"daily_budget": 150.0}})
