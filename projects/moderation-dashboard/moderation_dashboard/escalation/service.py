from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime

import httpx
from sqlalchemy import Row, create_engine, text
from sqlalchemy.orm import sessionmaker

from moderation_dashboard.api.models import Escalation
from moderation_dashboard.config import get_settings

logger = logging.getLogger(__name__)

_SEVERITY_MAP = {
    "severe_toxic": "high",
    "threat": "high",
    "obscene": "medium",
    "insult": "medium",
    "identity_hate": "medium",
    "toxic": "low",
    "clean": "low",
}


def _infer_severity(category: str, reason: str, confidence_max: float | None) -> str:
    if category in ("severe_toxic", "threat"):
        return "high"
    if category in ("obscene", "insult", "identity_hate"):
        return "medium"
    if reason == "model_disagreement":
        return "medium"
    return "low"


class EscalationService:
    def __init__(
        self,
        db_url: str,
        case_queue_api_url: str,
        confidence_threshold: float = 0.6,
        poll_interval_secs: float = 10.0,
    ) -> None:
        self._case_queue_api_url = case_queue_api_url
        self._confidence_threshold = confidence_threshold
        self._poll_interval_secs = poll_interval_secs
        self._running = True

        engine = create_engine(db_url)
        self._Session = sessionmaker(bind=engine)

    def run(self) -> None:
        import signal

        def _sigint(sig: int, frame: object) -> None:
            self._running = False

        signal.signal(signal.SIGINT, _sigint)
        logger.info(
            "Escalation service started (poll=%.0fs, conf_threshold=%.2f)",
            self._poll_interval_secs,
            self._confidence_threshold,
        )

        while self._running:
            try:
                self._poll_cycle()
            except Exception:
                logger.warning("Error in escalation poll cycle", exc_info=True)
            time.sleep(self._poll_interval_secs)

    def _poll_cycle(self) -> None:
        event_ids = self._get_unevaluated_event_ids()
        if not event_ids:
            return
        logger.info("Evaluating %d unescalated shadow events", len(event_ids))

        for event_id in event_ids:
            if not self._running:
                break
            try:
                shadow_rows = self._get_shadow_rows(event_id)
                if len(shadow_rows) < 2:
                    continue
                should_escalate, reason, confidence_max = self._evaluate_event(
                    event_id, shadow_rows
                )
                if not should_escalate:
                    # Write a null escalation to mark as evaluated (dedup)
                    # Actually — only write escalation rows when escalating; skip otherwise
                    # But then _get_unevaluated_event_ids will keep returning this event.
                    # Resolution: write a "no_escalation" row so we don't re-evaluate.
                    # For simplicity, write a skip record with reason="no_escalation".
                    self._write_escalation(event_id, "skip", "no_escalation", None)
                    continue

                content, category = self._get_event_content_and_category(event_id)
                verdicts = {row.model_name: row.predicted_label for row in shadow_rows}
                case_id = self._post_to_case_queue(
                    content, category, reason, confidence_max, verdicts
                )
                self._write_escalation(event_id, case_id, reason, confidence_max)
                logger.info("Escalated event %s as case %s (reason=%s)", event_id, case_id, reason)
            except Exception:
                logger.warning("Failed to process event_id=%s", event_id, exc_info=True)

    def _get_unevaluated_event_ids(self) -> list[str]:
        sql = text("""
            SELECT DISTINCT c.event_id
            FROM classifications c
            LEFT JOIN escalations e ON c.event_id = e.event_id
            WHERE c."group" = 'shadow'
              AND e.event_id IS NULL
            GROUP BY c.event_id
            HAVING COUNT(DISTINCT c.model_name) >= 2
            LIMIT 100
        """)
        with self._Session() as session:
            result = session.execute(sql)
            return [row[0] for row in result.fetchall()]

    def _get_shadow_rows(self, event_id: str) -> list[Row]:
        sql = text("""
            SELECT model_name, predicted_label, confidence
            FROM classifications
            WHERE event_id = :event_id AND "group" = 'shadow'
        """)
        with self._Session() as session:
            result = session.execute(sql, {"event_id": event_id})
            return list(result.fetchall())

    def _evaluate_event(
        self, event_id: str, shadow_rows: list[Row]
    ) -> tuple[bool, str, float | None]:
        labels = {row.predicted_label for row in shadow_rows}
        confidences = [row.confidence for row in shadow_rows]
        confidence_max = max(confidences)

        if len(labels) > 1:
            return True, "model_disagreement", None

        if confidence_max < self._confidence_threshold:
            return True, "low_confidence", confidence_max

        return False, "none", None

    def _get_event_content_and_category(self, event_id: str) -> tuple[str, str]:
        sql = text("""
            SELECT content, category
            FROM classifications
            WHERE event_id = :event_id
            LIMIT 1
        """)
        with self._Session() as session:
            result = session.execute(sql, {"event_id": event_id})
            row = result.fetchone()
            if row is None:
                raise ValueError(f"No classifications found for event_id={event_id!r}")
            return row.content, row.category

    def _post_to_case_queue(
        self,
        content: str,
        category: str,
        reason: str,
        confidence_max: float | None,
        verdicts: dict[str, int],
    ) -> str:
        severity = _infer_severity(category, reason, confidence_max)
        payload = {
            "content": content,
            "category": category,
            "severity": severity,
            "source": "moderation-dashboard",
            "meta": {
                "escalation_reason": reason,
                "confidence_max": confidence_max,
                "model_verdicts": verdicts,
            },
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{self._case_queue_api_url}/cases", json=payload)
            response.raise_for_status()
        return str(response.json()["id"])

    def _write_escalation(
        self,
        event_id: str,
        case_queue_case_id: str,
        escalation_reason: str,
        confidence_max: float | None,
    ) -> None:
        record = Escalation(
            id=str(uuid.uuid4()),
            event_id=event_id,
            case_queue_case_id=case_queue_case_id,
            escalation_reason=escalation_reason,
            confidence_max=confidence_max,
            created_at=datetime.now(UTC),
        )
        with self._Session() as session:
            session.add(record)
            session.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    service = EscalationService(
        db_url=settings.postgres_url_sync,
        case_queue_api_url=settings.case_queue_api_url,
        confidence_threshold=settings.escalation_confidence_threshold,
        poll_interval_secs=settings.escalation_poll_interval_secs,
    )
    service.run()
