# Implementation Plan

## **Purpose**

This document translates the architecture into an executable delivery plan:

- what to build first
- how to phase the work
- what documents to write
- recommended tech stack choices
- milestones, acceptance criteria, and risks

---

## **Extracted Implementation Notes (from Architecture)**

### **Why LangGraph-style orchestration fits**

- Explicit nodes/edges for deterministic routing
- Persistence/checkpointing enables replay
- Interrupts enable human-in-the-loop at controlled points

### **Why schema-first (Pydantic / PydanticAI patterns)**

- Turns “almost correct” LLM output into validation errors
- Makes remediation deterministic

### **Storage options**

- Event log: JSONL per run
- Snapshot: JSON per checkpoint
- Optional: SQLite/Postgres for queryability across runs

---

## **Delivery Strategy**

Build the system in layers. Each phase produces something shippable and testable, even if limited.

Key rule: **don’t build “smart” before you build “deterministic + observable”.**

Interlock’s value comes from correctness and traceability more than clever prompts.

---

## **Phase 0 — Foundations (Project Setup + Contracts)**

### **Goals**

- Lock down interfaces and schemas so everything downstream is stable.

### **Work items**

- Repo setup (lint, type checking, formatting, CI)
- Define **Run ID** concept + directory layout for run artifacts
- Create baseline schemas (Pydantic):
    - PinnedRequirements
    - Source
    - Evidence
    - Entities
    - Plan
    - CoverageReport
    - RunGovernance (budgets, retries, counters)
- Define event format:
    - tool calls (args hash, result hash)
    - validation results
    - delta payloads

### **Deliverables**

- schemas/ module with versioned models
- “hello run” that creates an empty snapshot + appends an initial event

### **Acceptance criteria**

- A run produces:
    - events.jsonl
    - snapshot.json
    - deterministic run folder structure

---

## **Phase 1 — Orchestrator Skeleton (FSM/Graph + State Bus)**

### **Goals**

- Deterministic orchestration that is replayable before adding lots of tools.

### **Work items**

- Implement graph/FSM with these minimal states:
    - PARSE_INTENT
    - VALIDATE_SCOPE (stubbed)
    - FETCH_JIRA (stubbed or mocked)
    - PIN_REQUIREMENTS (LLM structured extraction)
    - FAIL_CLOSED
- Add deterministic routing rules (no LLM routing)
- Add checkpointing:
    - snapshot persisted per state transition
    - append-only event log per transition
- Add retry policy and error signature tracking

### **Deliverables**

- Orchestrator runner (CLI) that executes the graph on a mocked ticket
- Event log + snapshot updates per state

### **Acceptance criteria**

- Same inputs → same states executed → same snapshot structure
- Failures stop deterministically with a structured failure report

---

## **Phase 2 — Connectors (Jira First, Then Confluence/GitHub)**

### **Goals**

- Real data plane integration with clean tool contracts.

### **Work items**

- Implement Jira connector (MCP-style interface if you use MCP):
    - get issue fields
    - list comments
    - list attachments metadata
    - identify linked resources
- Add Confluence connector:
    - fetch page by URL/id
    - search by query
- Add GitHub connector:
    - fetch PR
    - code search
    - fetch file content

### **Deliverables**

- tools/ layer with stable interfaces and normalized outputs
- Tool call logging into event log (args hash + result hash + minimal metadata)

### **Acceptance criteria**

- Can run end-to-end on a real Jira issue and create:
    - pinned requirements
    - list of sources (even if evidence isn’t built yet)

---

## **Phase 3 — Evidence Layer (Evidence-First Context)**

### **Goals**

- Stop passing raw dumps; compile evidence objects instead.

### **Work items**

- Implement BUILD_EVIDENCE_INDEX
    - chunking rules by source type
    - evidence object creation
    - provenance + locator population
- Add budget enforcement:
    - max evidence items
    - max evidence tokens estimate
    - max sources per type
    - max search rounds
- Implement COMPRESSION state:
    - merge/summarize evidence objects into fewer, higher-signal ones

### **Deliverables**

- Evidence index persisted inside snapshot + referenced in events
- Compression path that triggers automatically when budgets exceed

### **Acceptance criteria**

- Evidence objects are small, traceable, and budgeted
- A run never grows context unboundedly

---

## **Phase 4 — Planning + Verification (Grounding + Coverage)**

### **Goals**

- Make outputs trustworthy: “claims must cite evidence” + requirement coverage.

### **Work items**

- Implement GROUNDING_VALIDATE
    - plan step must include evidence_ids[]
    - uncited claims must be explicit assumptions[]
    - unresolved unknowns[] block progress
- Implement GENERATE_PLAN using structured output (Pydantic schema)
- Implement VERIFY_COVERAGE
    - map acceptance criteria → plan steps → validation/test steps → evidence IDs
    - define thresholds and failure routing

### **Deliverables**

- Structured plan object + coverage report
- Deterministic remediation routing when coverage fails

### **Acceptance criteria**

- No plan step ships without evidence OR explicit assumption
- 100% of acceptance criteria mapped (or run fails/interrupts)

---

## **Phase 5 — Observability + Debuggability**

### **Goals**

- Make runs easy to inspect and diagnose.

### **Work items**

- Run viewer output (CLI summary at minimum):
    - state transitions
    - tool calls
    - validation results
    - budgets/retries counters
- Metrics logging:
    - token usage per state
    - tool latency per connector
    - evidence counts and compression rate
- Optional: OpenTelemetry traces

### **Deliverables**

- “Run Summary” artifact per run
- Standard logs + structured metrics

### **Acceptance criteria**

- You can answer: “why did we fail?” in <2 minutes by reading artifacts

---

## **Phase 6 — Human-in-the-Loop (Interrupt + Resume)**

### **Goals**

- Controlled escalation instead of looping or guessing.

### **Work items**

- Add HUMAN_INTERRUPT state:
    - triggered by repeated failure signatures or unresolved unknowns
- Resume mechanism:
    - operator provides missing info or approves assumptions
    - run continues from checkpoint

### **Deliverables**

- Interactive CLI prompt or UI hook for interrupt/resume
- Logged human decisions as events

### **Acceptance criteria**

- Runs pause at deterministic points and resume without losing traceability

---

## **Phase 7 — Hardening + Productionization**

### **Goals**

- Reliability, security, scale, and cost control.

### **Work items**

- Secret management, connector auth hardening
- Caching tool results by hash
- Rate limiting + backoff
- Test suite:
    - golden runs (replay compares outputs)
    - schema tests
    - connector mocks
- Deployment packaging

### **Deliverables**

- Production-ready service mode (optional)
- Replay test harness

### **Acceptance criteria**

- Regression runs are stable
- Known failure modes handled (permissions, missing links, huge pages)

---

## **Recommended Tech Stack**

### **Core runtime**

- **Python 3.11+**
- Orchestration: **LangGraph** (preferred) or deterministic FSM framework
- Schemas/validation: **Pydantic** (+ optionally **PydanticAI patterns** for structured LLM output)
- LLM client: OpenAI SDK (or your existing stack)

### **Storage**

- Start: local filesystem
    - events.jsonl
    - snapshot.json (per checkpoint)
- Scale: SQLite/Postgres (query across runs, dashboards)

### **Tooling layer**

- MCP-style tool interfaces (fits your direction)
- Normalized tool outputs (avoid tool-specific shapes leaking into state)

### **Observability**

- structured logging (json logs)
- optional OpenTelemetry traces + metrics

---

## **Documentation Plan (What to Write)**

### **Already in progress**

- **Product Overview** (short, pain points + concept)
- **Architecture** (what it is, how components fit)

### **Add these docs**

1. **Implementation Plan** (this document)
2. **State Bus Reference**
    - schemas, event types, pinned vs working, governance fields
3. **FSM Reference**
    - state list, guards, retry/interrupt policy, routing table
4. **Tool Contracts**
    - Jira/Confluence/GitHub tool interface + normalized response shapes
5. **Runbook**
    - how to run locally, how to debug failures, how to replay
6. **ADR Log**
    - decisions (LangGraph choice, storage choice, evidence budgets, etc.)

---

## **Milestones (Suggested)**

### **Milestone A: Deterministic run skeleton (Phases 0–1)**

- event log + snapshot + pinned requirements extraction

### **Milestone B: Real Jira integration (Phase 2)**

- fetch ticket + sources list

### **Milestone C: Evidence index + budgets (Phase 3)**

- evidence-first context compiled

### **Milestone D: Grounded plan + coverage checks (Phase 4)**

- end-to-end reliable output

### **Milestone E: Debuggable + interruptable (Phases 5–6)**

- production-ready operator experience

---

## **Risks / Watchouts**

- Evidence explosion (solved via budgets + compression state)
- Tool permission failures (must fail closed with clear missing-access report)
- Over-reliance on LLM routing (keep routing deterministic)
- Schema drift (version schemas, keep migrations explicit)