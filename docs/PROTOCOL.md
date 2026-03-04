# Interlock MCP Protocol

This document defines how an agent must interact with the Interlock MCP server.

## Goal

Use Interlock as the single authority for:

1. State transitions
2. Validation results
3. Next-stage agent guidance

The agent may fill payload fields, but never controls stage progression directly.

## Tools

### `interlock_begin_run(ticket_id, run_id?)`

Starts a run and returns a clean `ticket.json` initialized at `fetch_ticket`.

### `interlock_submit_ticket(ticket_json)`

Validates submitted `ticket.json` for the current stage and returns:

- Updated `ticket_json`
- `next_state`
- `next_role` (guidance for next stage)
- `gate_result`

### `interlock_next_step(ticket_json)`

Backward-compatible alias for `interlock_submit_ticket`.

## Source of Truth

Local file: `tickets/ticket.json`

Rules:

1. Always submit the full file content to Interlock.
2. Always replace local file with server-returned `ticket_json`.
3. Never mutate `state`, `agent_role`, `required_fields`, or `next_stage_fields` locally.

## Workflow

1. If no local ticket exists, call `interlock_begin_run`.
2. Save returned `ticket_json` to `tickets/ticket.json`.
3. Read `required_fields` and `next_role`.
4. Fill only `payload` for the current stage.
5. Call `interlock_submit_ticket(ticket_json)`.
6. Persist returned `ticket_json`.
7. Repeat until terminal state.

## Terminal States

- `complete`: run finished successfully.
- `fail_closed`: blocking failure; stop and surface `invalidation_report`.

## Response Handling

### Gate retry (`gate_result.status == "retry"`)

- Do not advance manually.
- Fix missing/invalid fields from `gate_result`.
- Resubmit.

### Gate stop / fail-closed

- Stop execution.
- Report `reason`, `next_state`, and `invalidation_report`.

### Success transition

- Use `next_role` as stage guidance.
- Continue with returned `state`.

## Non-Negotiable Constraints

1. No state transition without Interlock response.
2. No local override of server-controlled fields.
3. No partial ticket submissions.
4. Every loop iteration must use the latest server-returned `ticket.json`.

## Minimal Loop Example

1. `begin_run` -> get `fetch_ticket` ticket.
2. Fill `payload` required by `fetch_ticket`.
3. `submit_ticket` -> receive `extract_requirements` + next role.
4. Repeat until `complete` or `fail_closed`.
