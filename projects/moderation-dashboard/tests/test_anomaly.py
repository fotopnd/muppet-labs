from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from moderation_dashboard.anomaly.detector import RollingWindowDetector, WindowState


def _make_detector(**kwargs) -> RollingWindowDetector:
    """Construct a RollingWindowDetector without touching Kafka or Postgres."""
    with patch("moderation_dashboard.anomaly.detector.Consumer"), patch(
        "moderation_dashboard.anomaly.detector.create_engine"
    ), patch("moderation_dashboard.anomaly.detector.sessionmaker") as mock_sm:
        det = RollingWindowDetector(
            bootstrap_servers="localhost:9092",
            topic="test-topic",
            db_url="postgresql://x",
            **kwargs,
        )
    det._Session = MagicMock()
    return det


class TestComputeZscore:
    def setup_method(self):
        self.det = _make_detector()

    def test_empty_history_returns_zero(self):
        assert self.det._compute_zscore(5.0, []) == 0.0

    def test_single_item_returns_zero(self):
        assert self.det._compute_zscore(5.0, [3.0]) == 0.0

    def test_zero_std_returns_zero(self):
        assert self.det._compute_zscore(5.0, [4.0, 4.0, 4.0]) == 0.0

    def test_normal_case(self):
        # mean=12.5, population std=sqrt(18.75)≈4.330; z=(25-12.5)/4.330≈2.887
        history = [10.0, 10.0, 10.0, 20.0]
        z = self.det._compute_zscore(25.0, history)
        assert z == pytest.approx(2.887, rel=1e-3)


class TestWindowBoundary:
    def setup_method(self):
        self.det = _make_detector(window_minutes=5)

    def test_duration_equals_window_minutes(self):
        ts = datetime(2024, 1, 1, 12, 3, 45, tzinfo=UTC)
        start, end = self.det._window_boundary(ts)
        delta = end - start
        assert delta.total_seconds() == 5 * 60

    def test_start_is_floored_to_window(self):
        ts = datetime(2024, 1, 1, 12, 3, 45, tzinfo=UTC)
        start, _ = self.det._window_boundary(ts)
        assert start == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    def test_end_equals_start_plus_window(self):
        ts = datetime(2024, 1, 1, 12, 7, 0, tzinfo=UTC)
        start, end = self.det._window_boundary(ts)
        assert start == datetime(2024, 1, 1, 12, 5, 0, tzinfo=UTC)
        assert end == datetime(2024, 1, 1, 12, 10, 0, tzinfo=UTC)


class TestCheckSignal:
    def setup_method(self):
        self.det = _make_detector(min_history=3, zscore_threshold=2.0)

    def _make_state(self) -> WindowState:
        t = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        return WindowState(
            window_start=t,
            window_end=t,
        )

    def test_no_flag_below_min_history(self):
        state = self._make_state()
        with patch.object(self.det, "_write_flag") as mock_write:
            # Only 2 calls — history will be [1.0, 1.0]; min_history=3 means no flag
            self.det._check_signal("vol", 1.0, state)
            self.det._check_signal("vol", 1.0, state)
            mock_write.assert_not_called()

    def test_flag_written_when_zscore_exceeds_threshold(self):
        state = self._make_state()
        with patch.object(self.det, "_write_flag") as mock_write:
            # Varied history (non-zero std) so the spike produces a large z-score
            for v in [8.0, 12.0, 9.0, 11.0, 10.0]:
                self.det._check_signal("vol", v, state)
            # Spike: z >> threshold
            self.det._check_signal("vol", 100.0, state)
            mock_write.assert_called_once()
            call_kwargs = mock_write.call_args.kwargs
            assert call_kwargs["signal_name"] == "vol"
            assert abs(call_kwargs["z_score"]) > 2.0

    def test_no_flag_when_zscore_within_threshold(self):
        state = self._make_state()
        with patch.object(self.det, "_write_flag") as mock_write:
            for v in [10.0, 10.5, 10.2, 10.1, 9.9, 10.3]:
                self.det._check_signal("vol", v, state)
            mock_write.assert_not_called()
