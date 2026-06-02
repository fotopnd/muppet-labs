from __future__ import annotations

from pydantic import BaseModel


class ModerationEvent(BaseModel):
    event_id: str
    text: str
    label: int | None = None
    label_detail: dict[str, float] | None = None
