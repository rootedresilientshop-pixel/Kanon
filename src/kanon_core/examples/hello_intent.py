from kanon_sdk.intent import Intent, Objective, Constraint

# Define a Mission: Optimize a marketing spend
marketing_mission = Intent(
    id="mkt-001",
    objective=Objective(name="ROAS", target="maximize", metric="revenue"),
    constraints=[
        Constraint(attribute="daily_budget", operator="<=", value=100.0),
        Constraint(attribute="platform", operator="in", value=["instagram", "linkedin"]),
        Constraint(attribute="risk_score", operator="<", value=0.2),
    ],
    mode="certification",
)

print(f"Generated Kanon Intent: {marketing_mission.id}")
print(marketing_mission.to_json())