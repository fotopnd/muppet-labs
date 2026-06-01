from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException

from app.models import ActorRole


@dataclass(frozen=True)
class Actor:
    id: str
    role: ActorRole


async def get_actor(
    x_actor_id: str = Header(),
    x_actor_role: str = Header(),
) -> Actor:
    try:
        role = ActorRole(x_actor_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {x_actor_role!r}")
    return Actor(id=x_actor_id, role=role)
