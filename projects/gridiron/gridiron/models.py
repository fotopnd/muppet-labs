from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BOOLEAN,
    CHAR,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Conglomerate(Base):
    __tablename__ = "conglomerates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(CHAR(3), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    network: Mapped[str] = mapped_column(Text, nullable=False)
    region: Mapped[str] = mapped_column(Text, nullable=False)
    primary_color: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    secondary_color: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    tertiary_color: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    programs: Mapped[list["Program"]] = relationship(back_populates="conglomerate")


class Program(Base):
    __tablename__ = "programs"
    __table_args__ = (
        CheckConstraint("tier IN (1, 2)", name="ck_programs_tier"),
        CheckConstraint("prestige BETWEEN 1 AND 5", name="ck_programs_prestige"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conglomerate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conglomerates.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    emoji: Mapped[str] = mapped_column(Text, nullable=False)
    mascot: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    tier: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    elo_seed_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    elo_seed_max: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    prestige: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    founded_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    primary_color: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    secondary_color: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    stadium_name: Mapped[str] = mapped_column(Text, nullable=False)
    stadium_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    conglomerate: Mapped["Conglomerate"] = relationship(back_populates="programs")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1 AND 4", name="ck_players_year"),
        CheckConstraint("alpha BETWEEN 0.0 AND 1.0", name="ck_players_alpha"),
        CheckConstraint("delta BETWEEN 0.0 AND 1.0", name="ck_players_delta"),
        CheckConstraint("sigma BETWEEN 0.0 AND 1.0", name="ck_players_sigma"),
        CheckConstraint("psi BETWEEN 0.0 AND 1.0", name="ck_players_psi"),
        CheckConstraint("omega BETWEEN 0.0 AND 1.0", name="ck_players_omega"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    jersey_num: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    # Secret attributes — obfuscated column names; never exposed in API responses
    alpha: Mapped[float] = mapped_column(Float, nullable=False)   # clutch
    delta: Mapped[float] = mapped_column(Float, nullable=False)   # upside
    sigma: Mapped[float] = mapped_column(Float, nullable=False)   # consistency
    psi: Mapped[float] = mapped_column(Float, nullable=False)     # leadership
    omega: Mapped[float] = mapped_column(Float, nullable=False)   # rivalry_dna
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    program: Mapped["Program"] = relationship(back_populates="players")


# Wire back-reference on Program
Program.players = relationship("Player", back_populates="program")


class Coach(Base):
    __tablename__ = "coaches"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 0.0 AND 1.0", name="ck_coaches_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    program: Mapped["Program"] = relationship(back_populates="coaches")


class Booster(Base):
    __tablename__ = "boosters"
    __table_args__ = (
        CheckConstraint("influence BETWEEN 0.0 AND 1.0", name="ck_boosters_influence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    influence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    program: Mapped["Program"] = relationship(back_populates="boosters")


# Wire back-references on Program for staff
Program.coaches = relationship("Coach", back_populates="program")
Program.boosters = relationship("Booster", back_populates="program")


class RivalryPair(Base):
    """Canonical cross-tier/cross-conf rivalry pairings, seeded at league genesis."""

    __tablename__ = "rivalry_pairs"
    __table_args__ = (
        CheckConstraint("program_a_id < program_b_id", name="ck_rivalry_pairs_order"),
    )

    program_a_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), primary_key=True
    )
    program_b_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), primary_key=True
    )


class Game(Base):
    """A single scheduled or completed game between two programs."""

    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint("week BETWEEN 1 AND 26", name="ck_games_week_range"),
        CheckConstraint("home_program_id != away_program_id", name="ck_games_no_self_play"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    home_program_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=True
    )
    away_program_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=True
    )
    is_rivalry: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, server_default="false")
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="scheduled")
    home_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    away_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
