# Interlock
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-workshop--project-lightgrey)](#)
[![Jira](https://img.shields.io/badge/integrates-Jira-blue)](#)

Interlock is a Jira-native AI companion that supports engineers throughout the lifecycle of complex tickets by guiding reasoning, structuring discussion, and preserving context directly inside Jira comments.

Instead of private, ephemeral AI sessions, Interlock governs agent-assisted work at the ticket level, making decisions, progress, and dependencies visible and reusable.

---

## Motivation

AI assistants are increasingly used by engineers to reason about Jira tickets, but most interactions happen in private sessions that are not visible, persisted, or reusable.

As a result:
- Reasoning and decisions are lost after the session ends
- Other engineers cannot learn from prior analysis
- Tickets capture outcomes, but not the process that led to them

Interlock addresses this gap by embedding AI assistance directly into Jira tickets, ensuring that reasoning is shared, auditable, and preserved.

---

## What Interlock Does

Interlock acts as a step-by-step companion during ticket resolution.

At a high level, it:
- Scans the ticket and retrieves relevant context (similar tickets, documentation, discussions)
- Generates a concise problem summary and possible resolution strategies
- Deepens analysis after a strategy is selected, including dependencies and risks
- Breaks the chosen approach into tasks and acceptance criteria
- Accompanies the assignee during execution with structured progress updates

All interaction happens through Jira comments (internal or public), keeping the entire process transparent.

---

## What Interlock Does *Not* Do

Interlock is intentionally constrained.

It does **not**:
- Design solutions or architectures
- Generate or modify code
- Make autonomous decisions
- Operate outside Jira tickets
- Run private or hidden agent sessions

Human engineers remain fully responsible for judgment and implementation.

---

## Core Principles

- **Ticket-level agent sessions**  
  Each Jira ticket is a single, governed agent session.

- **Comment-first interaction**  
  All agent output is posted as Jira comments.

- **Transparency over autonomy**  
  Visibility and traceability are prioritized over automation.

- **Human-in-the-loop by design**  
  Engineers own all decisions.

---

## High-Level Architecture

- Jira Extension (UI and ticket integration)
- Issue Analyzer (extracts intent and signals)
- Context Builder (retrieves organizational knowledge)
- Companion Reasoning Layer (summarization and structuring)
- Comment Orchestrator (controls flow and visibility)
- Ticket-scoped state and policy enforcement

All components operate within the scope of a single Jira ticket.

---

## External Dependencies

- Jira (system of record)
- Organizational knowledge hub (e.g. documentation, past tickets)
- Language model provider for constrained reasoning

No integration with code repositories or deployment systems is required.

---

## Project Status

This project is developed as part of an academic workshop.

The focus is on:
- Conceptual clarity
- System design
- Governance of AI-assisted workflows

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
