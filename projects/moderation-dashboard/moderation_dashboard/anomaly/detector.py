from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import numpy as np
from confluent_kafka import Consumer, KafkaError, KafkaException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from moderation_dashboard.api.models import AnomalyFlag
from moderation_dashboard.config import get_settings
from moderation_dashboard.types import ModerationEvent

logger = logging.getLogger(__name__)


@dataclass
class WindowState:
    window_start: datetime
    window_end: datetime
    event_count: int = 0
    category_counts: dict[str, int] = field(default_factory=dict)


class RollingWindowDetector:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        db_url: str,
        window_minutes: int = 5,
        zscore_threshold: float = 3.0,
        min_history: int = 10,
    ) -> None:
        self._topic = topic
        self._window_minutes = window_minutes
        self._zscore_threshold = zscore_threshold
        self._min_history = min_history
        self._running = True

        engine = create_engine(db_url)
        self._Session = sessionmaker(bind=engine)

        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": "moderation-anomaly",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )

        # signal_name → list of observed values (one per completed window)
        self._window_history: dict[str, list[float]] = {}
        self._current_window: WindowState | None = None

    def run(self) -> None:
        import signal

        def _sigint(sig: int, frame: object) -> None:
            self._running = False

        signal.signal(signal.SIGINT, _sigint)
        self._consumer.subscribe([self._topic])
        logger.info(
            "Anomaly detector started (window=%dmin, threshold=%.1f)",
            self._window_minutes,
            self._zscore_threshold,
        )

        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())

                try:
                    event = ModerationEvent.model_validate_json(msg.value())
                    self._process_event(event)
                    self._consumer.commit(asynchronous=False)
                except Exception:
                    logger.warning("Failed to process event in anomaly detector", exc_info=True)
        finally:
            self._consumer.close()
            logger.info("Anomaly detector stopped.")

    def _window_boundary(self, ts: datetime) -> tuple[datetime, datetime]:
        total_seconds = ts.timestamp()
        window_secs = self._window_minutes * 60
        window_start_ts = (total_seconds // window_secs) * window_secs
        window_start = datetime.fromtimestamp(window_start_ts, tz=UTC)
        window_end = window_start + timedelta(minutes=self._window_minutes)
        return window_start, window_end

    def _process_event(self, event: ModerationEvent) -> None:
        w_start, w_end = self._window_boundary(event.published_at)

        if self._current_window is None:
            self._current_window = WindowState(window_start=w_start, window_end=w_end)

        if w_start > self._current_window.window_start:
            # Event is in a new window — flush the completed window first
            self._flush_window(self._current_window)
            self._current_window = WindowState(window_start=w_start, window_end=w_end)

        self._current_window.event_count += 1
        cat = event.category
        self._current_window.category_counts[cat] = (
            self._current_window.category_counts.get(cat, 0) + 1
        )

    def _flush_window(self, state: WindowState) -> None:
        total = state.event_count
        self._check_signal("event_volume", float(total), state)

        for category, count in state.category_counts.items():
            rate = count / max(total, 1)
            self._check_signal(f"category_rate_{category}", rate, state)

        disagreement_rate = self._get_shadow_disagreement_rate(state.window_start, state.window_end)
        self._check_signal("disagreement_rate", disagreement_rate, state)

    def _check_signal(self, signal_name: str, value: float, state: WindowState) -> None:
        history = self._window_history.setdefault(signal_name, [])
        history.append(value)
        # Keep only what we need for computing stats — not trimming to keep full baseline
        z = self._compute_zscore(value, history[:-1])  # exclude current value from baseline

        if len(history) >= self._min_history and abs(z) > self._zscore_threshold:
            baseline = history[:-1]
            self._write_flag(
                state=state,
                signal_name=signal_name,
                z_score=z,
                value=value,
                baseline_mean=float(np.mean(baseline)),
                baseline_std=float(np.std(baseline)),
            )

    def _compute_zscore(self, value: float, history: list[float]) -> float:
        if len(history) < 2:
            return 0.0
        arr = np.array(history)
        std = float(np.std(arr))
        if std == 0.0:
            return 0.0
        return float((value - np.mean(arr)) / std)

    def _get_shadow_disagreement_rate(self, window_start: datetime, window_end: datetime) -> float:
        sql = text("""
            SELECT
                COUNT(CASE WHEN model_count >= 2 AND label_count > 1 THEN 1 END)::float
                / NULLIF(COUNT(CASE WHEN model_count >= 2 THEN 1 END), 0)
            FROM (
                SELECT
                    event_id,
                    COUNT(DISTINCT model_name) AS model_count,
                    COUNT(DISTINCT predicted_label) AS label_count
                FROM classifications
                WHERE "group" = 'shadow'
                  AND created_at >= :window_start
                  AND created_at < :window_end
                GROUP BY event_id
            ) t
        """)
        with self._Session() as session:
            result = session.execute(sql, {"window_start": window_start, "window_end": window_end})
            rate = result.scalar()
            return float(rate) if rate is not None else 0.0

    def _write_flag(
        self,
        state: WindowState,
        signal_name: str,
        z_score: float,
        value: float,
        baseline_mean: float,
        baseline_std: float,
    ) -> None:
        now = datetime.now(UTC)
        flag = AnomalyFlag(
            id=str(uuid.uuid4()),
            window_start=state.window_start,
            window_end=state.window_end,
            signal_name=signal_name,
            z_score=z_score,
            value=value,
            baseline_mean=baseline_mean,
            baseline_std=baseline_std,
            created_at=now,
        )
        with self._Session() as session:
            session.add(flag)
            session.commit()
        logger.info(
            "Anomaly flag: signal=%s z=%.2f value=%.3f window=%s",
            signal_name,
            z_score,
            value,
            state.window_start.isoformat(),
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    detector = RollingWindowDetector(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        topic=settings.kafka_topic,
        db_url=settings.postgres_url_sync,
        window_minutes=settings.anomaly_window_minutes,
        zscore_threshold=settings.anomaly_zscore_threshold,
        min_history=settings.anomaly_min_history_windows,
    )
    detector.run()
