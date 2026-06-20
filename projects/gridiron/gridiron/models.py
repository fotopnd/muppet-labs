from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Models are defined here by the implementer role.
# Engine-generated entities (Team, Player, Game, Play, Season) live here.
# Engine logic stays in gridiron/engine/ — models only hold the DB schema.
