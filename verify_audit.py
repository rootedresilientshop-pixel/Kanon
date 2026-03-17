import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def verify_log_entry(entry_json):
    entry = json.loads(entry_json)
    sig_hex = entry.pop("signature", None)
    pk_hex = entry.pop("public_key", None)

    if not pk_hex:
        intent_id = entry.get("intent_id", "<unknown>")
        print(f"Entry {intent_id}: UNVERIFIABLE: Missing Public Key")
        return False

    if not sig_hex:
        intent_id = entry.get("intent_id", "<unknown>")
        print(f"Entry {intent_id}: TAMPERED OR INVALID")
        return False

    sig = bytes.fromhex(sig_hex)
    pk_bytes = bytes.fromhex(pk_hex)

    payload_obj = {
        "timestamp": entry.get("timestamp"),
        "intent_id": entry.get("intent_id"),
        "objective": entry.get("objective"),
        "mode": entry.get("mode"),
        "version": entry.get("version"),
        "action_params": entry.get("action_params"),
        "result": entry.get("result"),
        "reason": entry.get("reason"),
    }
    payload = canonical_json(payload_obj).encode("utf-8")

    try:
        vk = Ed25519PublicKey.from_public_bytes(pk_bytes)
        vk.verify(sig, payload)
        print(f"Entry {entry['intent_id']}: AUTHENTICATED")
        return True
    except Exception:
        print(f"Entry {entry['intent_id']}: TAMPERED OR INVALID")
        return False


def main():
    with open("kanon_audit.log", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                verify_log_entry(line)


if __name__ == "__main__":
    main()
