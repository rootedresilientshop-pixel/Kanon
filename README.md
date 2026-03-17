# Kanon Sentry

Kanon Sentry is a deterministic, local-first safety layer for agentic AI. It is designed for developers who prioritize cryptographic accountability and on-device enforcement over cloud-based alignment.

This repository is the **Phase 1: Sovereign** release. The focus is a minimal, inspectable kernel with an auditable trail of every enforcement decision. Expect sharp edges; the goal is correctness and traceability first.

## What It Does
- Validates actions against explicit intent constraints.
- Emits signed audit log entries for every decision.
- Keeps enforcement logic deterministic and transparent.

## Modular Architecture
Phase 2 is now live. The `kanon_thinktank` module adds a cryptographically secured blackboard for multi-agent systems, enabling shared context and audited coordination across agents without leaving the local runtime.

## Quick Start
1. Set the signing seed:
   - `KANON_SEED` must be a 64-hex-character value (32 bytes).
2. Install locally:
   - `pip install -e .`
3. Run the example:
   - `python test_enforcement.py`

## Philosophy
- **Local-First Sovereignty:** The kernel should run and be verifiable on your machine.
- **Deterministic Safety:** The rules are explicit; outcomes are reproducible.
- **Cryptographic Accountability:** Audit logs are signed and verifiable.

## Status
Phase 1: Sovereign. Built for builders who want a practical, auditable safety kernel today, not a promise of future alignment.