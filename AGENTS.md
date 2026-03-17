# AGENTS.md - Project Sovereignty & Pillars
> **Machine Status:** [4GB RAM Limited] - Execute one task at a time. No parallel agents.

## Three Pillars Mapping
- **Source:** D:\Projects\Kanon (Current Dir)
- **Environment:** D:\Environment\Kanon (Junctioned .vscode, .cache, .logs)
- **Tools:** D:\Tools (Ollama, CLI scripts)

## Operational Rules
- **Memory Hygiene:** If RAM > 3.2GB, stop and suggest a model unload or system restart.
- **Pathing:** NEVER create new dot-folders (.vscode, .git) in the root. If needed, create in D:\Environment and symlink back.
- **Verification:** Before "Finish," run a local verification script if available.

Reference: See D:\Projects\Architect Ecosystem\STACK.md for C#/.NET and Python standards.
