from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from red_team_platform.models import Attack, Base, Run, RunSession

TEST_DB_URL = "postgresql+asyncpg://redteam:redteam@localhost:5433/redteam_test"


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
    async with eng.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("DROP MATERIALIZED VIEW IF EXISTS coverage_summary")
        )
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # Create coverage_summary view manually (not in metadata)
        await conn.execute(
            __import__("sqlalchemy").text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS coverage_summary AS
            SELECT
                a.harm_category, a.strategy,
                COUNT(*) AS total_runs,
                SUM(CASE WHEN r.jailbreak_success THEN 1 ELSE 0 END) AS total_successes,
                AVG(r.jailbreak_success::int)::float AS asr
            FROM runs r JOIN attacks a ON r.attack_id = a.id
            GROUP BY a.harm_category, a.strategy
            """)
        )
        await conn.execute(
            __import__("sqlalchemy").text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uix_cov "
                "ON coverage_summary (harm_category, strategy)"
            )
        )
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def seeded_attack(db_session: AsyncSession) -> Attack:
    atk = Attack(
        source="sevdeawesome",
        source_id=f"sev-test-{uuid.uuid4()}",
        harm_category="toxic_language_hate_speech",
        strategy="DAN",
        attack_text="Test attack prompt",
    )
    db_session.add(atk)
    await db_session.flush()
    return atk


@pytest_asyncio.fixture
async def seeded_run(db_session: AsyncSession, seeded_attack: Attack) -> tuple[RunSession, Run]:
    sess = RunSession(model_name="qwen2.5-coder:7b", total_attacks=1, total_successes=1, asr=1.0)
    db_session.add(sess)
    await db_session.flush()

    run = Run(
        session_id=sess.id,
        attack_id=seeded_attack.id,
        model_name="qwen2.5-coder:7b",
        response_text="Jailbroken response",
        jailbreak_success=True,
        classifier_score=0.92,
        latency_ms=350,
    )
    db_session.add(run)
    await db_session.flush()
    return sess, run


@pytest.fixture
def mock_classifier(mocker):
    mocker.patch(
        "red_team_platform.runner.classifier.score",
        return_value=(True, 0.9),
    )


@pytest.fixture
def api_client(mock_classifier):
    from red_team_platform.api.main import create_app

    app = create_app()
    return TestClient(app)
