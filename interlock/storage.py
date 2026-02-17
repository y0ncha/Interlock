"""Artifact persistence for Interlock ticket.json workflow."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from interlock.schemas.ticket import Ticket

logger = logging.getLogger(__name__)


class ArtifactStore:
    """Store ticket snapshots and events for traceable runs."""

    def __init__(self, storage_dir: Path | str = "interlock_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir = self.storage_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        self.tickets_file = self.storage_dir / "tickets.jsonl"
        self.events_file = self.storage_dir / "events.jsonl"

    def _run_dir(self, run_id: str) -> Path:
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_ticket(self, ticket: Ticket) -> None:
        """Persist ticket snapshot both as run-local ticket.json and global JSONL."""
        run_dir = self._run_dir(ticket.run_id)
        ticket_path = run_dir / "ticket.json"
        ticket_path.write_text(ticket.to_json(pretty=True), encoding="utf-8")

        record = ticket.model_dump(mode="json")
        record["_saved_at"] = datetime.now(timezone.utc).isoformat()
        with self.tickets_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info("Saved ticket snapshot run_id=%s state=%s", ticket.run_id, ticket.state)

    def get_run_ticket(self, run_id: str) -> Ticket | None:
        """Load the latest run-local ticket.json for a run_id."""
        ticket_path = self.runs_dir / run_id / "ticket.json"
        if not ticket_path.exists():
            return None
        return Ticket.from_json(ticket_path.read_text(encoding="utf-8"))

    def save_event(
        self,
        *,
        run_id: str,
        event_type: str,
        state: str,
        details: dict | None = None,
    ) -> None:
        """Append a structured event to global and run-local event logs."""
        event = {
            "run_id": run_id,
            "event_type": event_type,
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

        with self.events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

        run_events = self._run_dir(run_id) / "events.jsonl"
        with run_events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

        logger.info("Saved event run_id=%s type=%s state=%s", run_id, event_type, state)
