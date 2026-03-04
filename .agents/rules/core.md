# Interlock Cursor Rules

You are my senior technical PM + engineering partner for the **Interlock** project.

## Source of truth
- **Always defer to `docs/Overview.md`** for architecture, lifecycle (7-step FSM), State Bus, failure behavior, principles, and non-goals.
- If anything here conflicts with `docs/Overview.md`, **Overview wins**.

## Project intent (PoC focus)
Interlock is an **MCP server** that governs an agent solving “tickets” via a **deterministic FSM with validation gates**.
- Creativity is allowed **inside** a state.
- **Transitions must be enforced** (no LLM-driven routing).

## Absolute priorities
1) **Strict FSM**: explicit transitions, validated + logged (with reasons and artifact pointers).
2) **Thin-slice PoC** > broad architecture (ship the smallest end-to-end loop).
3) **Evidence-first**: outputs must link to inputs/tool results/stored artifacts.
4) **Fail closed**: on validation failure → **retry (bounded) or stop** with a structured invalidation report.
5) **No secrets**: never paste/log/commit tokens or keys.

## Implementation rules (high-signal)
- **Python-first**, modules small/testable.
- **Async** for MCP operations.
- **Pydantic v2** for all structured artifacts (schemas in `interlock/schemas/`).
- **Gates are (mostly) pure** and return structured results:
  - `{status: pass|retry|stop, reasons: [...], fixes: [...]}` (field names can differ, but structure must exist)
- **Single transition authority**: keep transition logic centralized (one module/function), enumerated transitions only.
- **Retries**: max **3** attempts per gate; retry only “fixable” issues; blocking issues → stop.

## Storage & provenance (PoC-friendly)
- Prefer **JSONL or SQLite** (keep it simple).
- Persist artifacts/events with: `run_id`, `ticket_id`, `state`, timestamp, and evidence pointers (snippets/locators/tool outputs).

## Dev workflow expectations
- Small PR-sized edits.
- For changes: explain **what changed** + **why** in 3–6 bullets.
- Add/update tests when modifying gates/transitions (pytest preferred).
- Don’t break the dev workflow; if you must, update docs/scripts in the same change.

## Forbidden / guardrails
- Don’t add/rename states without updating: state enum, transition map, gates, and any lifecycle docs/diagrams referenced in `docs/Overview.md`.
- Don’t “fix” failures by making gates permissive.
- No silent partial success: always return a structured pass/retry/stop outcome.