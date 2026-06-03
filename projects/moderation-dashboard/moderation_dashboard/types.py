from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ModerationEvent(BaseModel):
    event_id: str  # uuid4 assigned by producer
    jigsaw_id: int  # CSV row index (0-based)
    content: str  # comment_text column
    ground_truth: int  # 0 | 1 — Jigsaw 'toxic' column
    category: str  # primary category from CATEGORY_PRIORITY
    published_at: datetime
