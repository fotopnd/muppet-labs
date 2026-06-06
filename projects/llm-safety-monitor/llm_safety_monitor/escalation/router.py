from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx

from llm_safety_monitor.config import Settings
from llm_safety_monitor.types import EscalationReason

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 2.0
_TIMEOUT_SECONDS = 10


def compute_escalation_reason(
    pair_label: int,
    pair_conf: float,
    prompt_label: int,
    prompt_conf: float,
    taxonomy_labels: list[str],
    has_response: bool,
) -> EscalationReason | None:
    """Pure function. Returns the appropriate escalation reason or None."""
    if not has_response:
        if prompt_label == 1 and prompt_conf > 0.7:
            return EscalationReason.ADVERSARIAL_PROMPT_FLAGGED
        return None

    if pair_label == 1 and prompt_label == 1:
        return EscalationReason.JAILBREAK
    if pair_label == 1 and prompt_label == 0:
        return EscalationReason.BENIGN_HARMFUL
    if pair_label == 0 and prompt_label == 1:
        return EscalationReason.LOG_ONLY
    # pair_label == 0, prompt_label == 0
    if pair_label == 0 and taxonomy_labels:
        return EscalationReason.MODEL_DISAGREEMENT
    if pair_label == 1 and not taxonomy_labels:
        return EscalationReason.MODEL_DISAGREEMENT
    return None


class EscalationPoller:
    """Daemon thread that polls DB every 2s, applies 2×2 matrix, posts to case-queue."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._running = False

    def run(self) -> None:
        from sqlalchemy import create_engine, select, text
        from sqlalchemy.orm import Session

        engine = create_engine(self._settings.SYNC_DATABASE_URL)
        self._running = True
        logger.info("EscalationPoller started")

        while self._running:
            try:
                with Session(engine) as session:
                    self._check_ready(session)
                    self._check_timed_out(session)
            except Exception as exc:
                logger.warning("EscalationPoller error: %s", exc, exc_info=True)
            time.sleep(_POLL_INTERVAL)

    def _check_ready(self, session: object) -> None:
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        assert isinstance(session, Session)

        rows = session.execute(
            text("""
                SELECT i.id
                FROM interactions i
                WHERE i.escalated = FALSE
                  AND EXISTS (
                      SELECT 1 FROM classifications c
                      WHERE c.event_id = i.id AND c.model_name = 'pair_classifier'
                  )
                  AND EXISTS (
                      SELECT 1 FROM classifications c
                      WHERE c.event_id = i.id AND c.model_name = 'prompt_detector'
                  )
                  AND EXISTS (
                      SELECT 1 FROM classifications c
                      WHERE c.event_id = i.id AND c.model_name = 'taxonomy_classifier'
                  )
                ORDER BY i.created_at
                LIMIT 100
            """)
        ).fetchall()

        for (event_id,) in rows:
            self._process_event(session, event_id)

    def _check_timed_out(self, session: object) -> None:
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        assert isinstance(session, Session)

        cutoff = datetime.now(UTC) - timedelta(seconds=_TIMEOUT_SECONDS)
        rows = session.execute(
            text("""
                SELECT i.id FROM interactions i
                WHERE i.escalated = FALSE
                  AND i.created_at < :cutoff
                  AND NOT (
                      EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='pair_classifier')
                      AND EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='prompt_detector')
                      AND EXISTS (SELECT 1 FROM classifications c WHERE c.event_id=i.id AND c.model_name='taxonomy_classifier')
                  )
                LIMIT 100
            """),
            {"cutoff": cutoff},
        ).fetchall()

        for (event_id,) in rows:
            logger.warning("Event %s timed out without all 3 classifications; skipping escalation", event_id)
            session.execute(
                text("UPDATE interactions SET escalated=TRUE WHERE id=:eid"),
                {"eid": event_id},
            )
        if rows:
            session.commit()

    def _process_event(self, session: object, event_id: object) -> None:
        from sqlalchemy import text
        from sqlalchemy.orm import Session

        assert isinstance(session, Session)

        # Load interaction
        interaction = session.execute(
            text("SELECT response_text FROM interactions WHERE id=:eid"),
            {"eid": event_id},
        ).fetchone()
        if not interaction:
            return

        has_response = bool(interaction[0])

        # Load the three classification results
        clf_rows = session.execute(
            text("""
                SELECT model_name, predicted_label, confidence, taxonomy_labels
                FROM classifications
                WHERE event_id=:eid AND model_name IN ('pair_classifier', 'prompt_detector', 'taxonomy_classifier')
            """),
            {"eid": event_id},
        ).fetchall()

        clfs = {row[0]: {"label": row[1], "conf": row[2], "taxonomy": row[3]} for row in clf_rows}

        pair = clfs.get("pair_classifier", {})
        prompt = clfs.get("prompt_detector", {})
        taxonomy = clfs.get("taxonomy_classifier", {})

        reason = compute_escalation_reason(
            pair_label=pair.get("label", 0),
            pair_conf=pair.get("conf", 0.0),
            prompt_label=prompt.get("label", 0),
            prompt_conf=prompt.get("conf", 0.0),
            taxonomy_labels=taxonomy.get("taxonomy") or [],
            has_response=has_response,
        )

        if reason and reason != EscalationReason.LOG_ONLY:
            self._post_to_case_queue(event_id, reason)

        session.execute(
            text("UPDATE interactions SET escalated=TRUE, escalation_reason=:reason WHERE id=:eid"),
            {"reason": reason.value if reason else None, "eid": event_id},
        )
        session.commit()

        if reason:
            logger.info("Event %s escalated: %s", event_id, reason)

    def _post_to_case_queue(self, event_id: object, reason: EscalationReason) -> None:
        severity_map = {
            EscalationReason.JAILBREAK: "critical",
            EscalationReason.BENIGN_HARMFUL: "high",
            EscalationReason.MODEL_DISAGREEMENT: "medium",
            EscalationReason.ADVERSARIAL_PROMPT_FLAGGED: "medium",
        }
        try:
            httpx.post(
                f"{self._settings.CASE_QUEUE_URL}/api/cases",
                json={
                    "content": f"LLM safety escalation: {reason.value}",
                    "source": "llm-safety-monitor",
                    "severity": severity_map.get(reason, "low"),
                    "metadata": {"event_id": str(event_id), "reason": reason.value},
                },
                timeout=5.0,
            )
        except Exception as exc:
            logger.warning("Failed to post to case-queue for event %s: %s", event_id, exc, exc_info=True)

    def stop(self) -> None:
        self._running = False
