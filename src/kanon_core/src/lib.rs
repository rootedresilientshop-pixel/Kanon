use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs::OpenOptions;
use std::io::Write;
use chrono::Utc;
use ed25519_dalek::{Signer, SigningKey};
use serde::de::Error as _;
use serde_json::Value as JsonValue;

#[derive(Debug, Serialize, Deserialize)]
pub struct Constraint {
    pub attribute: String,
    pub operator: String,
    pub value: serde_json::Value,
    pub priority: i32,
}

fn objective_from_any<'de, D>(deserializer: D) -> Result<String, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = JsonValue::deserialize(deserializer)?;
    match value {
        JsonValue::String(s) => Ok(s),
        other => serde_json::to_string(&other)
            .map_err(D::Error::custom),
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Intent {
    pub id: String,
    #[serde(deserialize_with = "objective_from_any")]
    pub objective: String,
    pub mode: String,
    pub version: String,
    pub constraints: Vec<Constraint>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProposedAction {
    pub params: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct State {
    pub values: HashMap<String, serde_json::Value>,
}

#[derive(Serialize)]
struct AuditEntry {
    timestamp: String,
    intent_id: String,
    objective: String,
    mode: String,
    version: String,
    action_params: serde_json::Value,
    result: String,
    reason: Option<String>,
    public_key: String,
    signature: String,
}

// Sign a serialized payload and return a hex-encoded signature.
fn sign_entry(payload: &str, signing_key: &SigningKey) -> String {
    let signature = signing_key.sign(payload.as_bytes());
    hex::encode(signature.to_bytes())
}

#[derive(Debug)]
enum SafetyError {
    UnsupportedOperator(String),
}

impl std::fmt::Display for SafetyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SafetyError::UnsupportedOperator(op) => {
                write!(f, "Unsupported operator: {}", op)
            }
        }
    }
}

fn load_signing_key() -> SigningKey {
    let seed_hex = env::var("KANON_SEED")
        .expect("Sovereign Sentry requires KANON_SEED for integrity.");
    let seed_bytes = hex::decode(seed_hex.trim())
        .expect("Invalid KANON_SEED; expected hex string.");
    let seed: [u8; 32] = seed_bytes
        .as_slice()
        .try_into()
        .expect("Invalid KANON_SEED length; expected 32 bytes.");
    SigningKey::from_bytes(&seed)
}

fn canonicalize_json(value: &JsonValue) -> JsonValue {
    match value {
        JsonValue::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let mut new_map = serde_json::Map::new();
            for key in keys {
                if let Some(child) = map.get(key) {
                    new_map.insert(key.clone(), canonicalize_json(child));
                }
            }
            JsonValue::Object(new_map)
        }
        JsonValue::Array(arr) => {
            JsonValue::Array(arr.iter().map(canonicalize_json).collect())
        }
        _ => value.clone(),
    }
}

pub struct Sentry;

impl Sentry {
    /// The heart of Kanon: Checks if an action violates any intent constraints.
    pub fn validate(intent: &Intent, action: &ProposedAction, state: &State) -> Result<bool, String> {
        for constraint in &intent.constraints {
            if constraint.attribute == "total_daily_spend" {
                let current_spend = state
                    .values
                    .get("current_spend")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0);
                let proposed_spend = action
                    .params
                    .get("amount")
                    .and_then(|v| v.as_f64())
                    .unwrap_or(0.0);
                let limit = constraint.value.as_f64().unwrap_or(0.0);

                if current_spend + proposed_spend > limit {
                    let err = format!(
                        "Dynamic Violation: Total spend would reach {}",
                        current_spend + proposed_spend
                    );
                    Self::log_event(intent, action, &Err(err.clone()));
                    return Err(err);
                }
            }
        }

        let mut result = Ok(true);

        for constraint in &intent.constraints {
            if constraint.attribute == "total_daily_spend" {
                // This constraint is validated dynamically against current state.
                continue;
            }

            let action_val = action.params.get(&constraint.attribute);

            match action_val {
                Some(val) => {
                    // Basic numeric comparison logic for Step 3
                    match Self::check_constraint(constraint, val) {
                        Ok(is_allowed) => {
                            if !is_allowed {
                                result = Err(format!(
                                    "Constraint violation: {} {} {:?}",
                                    constraint.attribute, constraint.operator, constraint.value
                                ));
                                break;
                            }
                        }
                        Err(e) => {
                            result = Err(e.to_string());
                            break;
                        }
                    }
                }
                None => {
                    // If a constraint exists but the action doesn't provide the value, block it.
                    result = Err(format!(
                        "Missing required attribute: {}",
                        constraint.attribute
                    ));
                    break;
                }
            }
        }

        // Always audit validation attempts, including failures.
        Self::log_event(intent, action, &result);
        result
    }

    fn log_event(intent: &Intent, action: &ProposedAction, result: &Result<bool, String>) {
        let signing_key = load_signing_key();
        let verifying_key = signing_key.verifying_key();

        let timestamp = Utc::now().to_rfc3339();
        let action_params = serde_json::to_value(&action.params).unwrap_or(serde_json::Value::Null);
        let result_str = if result.is_ok() {
            "PASS".to_string()
        } else {
            "FAIL".to_string()
        };
        let reason = result.as_ref().err().cloned();

        let mut payload_map = serde_json::Map::new();
        payload_map.insert("action_params".to_string(), action_params.clone());
        payload_map.insert("intent_id".to_string(), JsonValue::String(intent.id.clone()));
        payload_map.insert("mode".to_string(), JsonValue::String(intent.mode.clone()));
        payload_map.insert("objective".to_string(), JsonValue::String(intent.objective.clone()));
        payload_map.insert(
            "reason".to_string(),
            reason.clone()
                .map(JsonValue::String)
                .unwrap_or(JsonValue::Null),
        );
        payload_map.insert("result".to_string(), JsonValue::String(result_str.clone()));
        payload_map.insert("timestamp".to_string(), JsonValue::String(timestamp.clone()));
        payload_map.insert("version".to_string(), JsonValue::String(intent.version.clone()));

        let payload = canonicalize_json(&JsonValue::Object(payload_map));

        let payload_str = match serde_json::to_string(&payload) {
            Ok(v) => v,
            Err(_) => return,
        };

        let entry = AuditEntry {
            timestamp,
            intent_id: intent.id.clone(),
            objective: intent.objective.clone(),
            mode: intent.mode.clone(),
            version: intent.version.clone(),
            action_params,
            result: result_str,
            reason,
            public_key: hex::encode(verifying_key.to_bytes()),
            signature: sign_entry(&payload_str, &signing_key),
        };

        if let Ok(json) = serde_json::to_string(&entry) {
            if let Ok(mut file) = OpenOptions::new()
                .create(true)
                .append(true)
                .open("kanon_audit.log")
            {
                let _ = writeln!(file, "{}", json);
            }
        }
    }

    fn check_constraint(c: &Constraint, val: &serde_json::Value) -> Result<bool, SafetyError> {
        // Simple numeric logic for MVP (we will expand this)
        match c.operator.as_str() {
            "<=" => Ok(val.as_f64().unwrap_or(0.0) <= c.value.as_f64().unwrap_or(-1.0)),
            ">=" => Ok(val.as_f64().unwrap_or(0.0) >= c.value.as_f64().unwrap_or(0.0)),
            "==" => Ok(val == &c.value),
            _ => Err(SafetyError::UnsupportedOperator(c.operator.clone())),
        }
    }
}

#[pyfunction]
fn validate_intent_json(intent_json: String, action_json: String, state_json: String) -> PyResult<bool> {
    // 1. Parse strings into Rust structs
    let intent: Intent = serde_json::from_str(&intent_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid Intent JSON: {}", e)))?;

    let action: ProposedAction = serde_json::from_str(&action_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid Action JSON: {}", e)))?;

    let state: State = serde_json::from_str(&state_json)
        .map_err(|e| PyValueError::new_err(format!("Invalid State JSON: {}", e)))?;

    // 2. Execute the Sentry
    match Sentry::validate(&intent, &action, &state) {
        Ok(is_valid) => Ok(is_valid),
        Err(e) => Err(PyValueError::new_err(e)),
    }
}

#[pymodule]
fn kanon_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_intent_json, m)?)?;
    Ok(())
}
