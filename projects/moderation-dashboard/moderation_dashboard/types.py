from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ModerationEvent(BaseModel):
    event_id: str  # uuid4 assigned by producer
    jigsaw_id: int  # CSV row index (0-based); -1 for live webhook events
    content: str  # comment_text column
    ground_truth: int | None  # 0|1 for Jigsaw rows; None for live webhook events
    category: str  # primary category from CATEGORY_PRIORITY; "unknown" for webhook
    published_at: datetime
