import json
from kanon_sdk.intent import Intent, Objective, Constraint, validate_with_context
from kanon_sdk.observer import SafetyObserver


observer = SafetyObserver()

# Define Global Limit: Total Spend cannot exceed 500
intent = Intent(
    id="global-guard-001",
    objective=Objective(name="Safety", target="maintain", metric="stability"),
    constraints=[
        Constraint(attribute="total_daily_spend", operator="<=", value=500.0)
    ],
)

# Current state of the world
world_state = {"values": {"current_spend": 450.0}}

# The AI tries to spend 60.0 (450 + 60 = 510, which should FAIL)
sneaky_action = {"params": {"amount": 60.0}}

print(f"Current Spend: {world_state['values']['current_spend']}")
print(f"Attempting to add: {sneaky_action['params']['amount']}")

try:
    validate_with_context(intent, sneaky_action, world_state)
    print("Action Allowed.")
except ValueError as e:
    print(f"SENTRY DETECTED SALAMI ATTACK: {e}")
