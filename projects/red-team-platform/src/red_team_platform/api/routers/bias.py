from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import (
    BackTranslateIn,
    BackTranslateOut,
    BiasLangDetail,
    BiasScoreRow,
    BiasScoresOut,
    BiasTopicResponseOut,
)

router = APIRouter(tags=["bias"])


@router.get("/bias/scores", response_model=BiasScoresOut)
async def get_bias_scores(db: AsyncSession = Depends(get_db)) -> BiasScoresOut:
    rows_result = await db.execute(
        text("""
            SELECT
                bp.topic_id,
                bp.government,
                bp.label,
                MAX(CASE WHEN bds.language = 'zh' THEN bds.cosine_distance END) AS zh_score,
                MAX(CASE WHEN bds.language = 'ru' THEN bds.cosine_distance END) AS ru_score,
                MAX(CASE WHEN bds.language = 'ar' THEN bds.cosine_distance END) AS ar_score
            FROM bias_probes bp
            LEFT JOIN bias_divergence_scores bds ON bp.id = bds.probe_id
            GROUP BY bp.topic_id, bp.government, bp.label
            ORDER BY bp.government, bp.topic_id
        """)
    )
    rows = [
        BiasScoreRow(
            topic_id=row.topic_id,
            government=row.government,
            label=row.label,
            zh_score=row.zh_score,
            ru_score=row.ru_score,
            ar_score=row.ar_score,
        )
        for row in rows_result.mappings()
    ]

    # Most recent model name from any divergence score
    model_result = await db.execute(
        text("SELECT model_name FROM bias_divergence_scores ORDER BY created_at DESC LIMIT 1")
    )
    model_row = model_result.fetchone()
    scored_model = model_row[0] if model_row else None

    return BiasScoresOut(rows=rows, scored_model=scored_model)


@router.get("/bias/responses/{topic_id}", response_model=BiasTopicResponseOut)
async def get_bias_responses(
    topic_id: str,
    model: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> BiasTopicResponseOut:
    probe_result = await db.execute(
        text(
            "SELECT id, topic_id, government, label"
            " FROM bias_probes WHERE topic_id = :tid LIMIT 1"
        ),
        {"tid": topic_id},
    )
    probe_row = probe_result.mappings().first()
    if probe_row is None:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id!r} not found")

    resolved_model = model
    if resolved_model is None:
        m_result = await db.execute(
            text("SELECT model_name FROM bias_divergence_scores ORDER BY created_at DESC LIMIT 1")
        )
        m_row = m_result.fetchone()
        resolved_model = m_row[0] if m_row else None

    lang_result = await db.execute(
        text("""
            SELECT
                bpv.language,
                bpv.prompt_text,
                br.response_text,
                bds.cosine_distance
            FROM bias_prompt_variants bpv
            LEFT JOIN bias_responses br
                ON br.variant_id = bpv.id AND br.model_name = :model
            LEFT JOIN bias_divergence_scores bds
                ON bds.probe_id = bpv.probe_id
                AND bds.language = bpv.language
                AND bds.model_name = :model
            WHERE bpv.probe_id = :probe_id
            ORDER BY bpv.language
        """),
        {"probe_id": str(probe_row["id"]), "model": resolved_model},
    )

    languages: dict[str, BiasLangDetail] = {}
    for row in lang_result.mappings():
        languages[row["language"]] = BiasLangDetail(
            prompt=row["prompt_text"],
            response=row["response_text"],
            cosine_distance=row["cosine_distance"],
        )

    return BiasTopicResponseOut(
        topic_id=probe_row["topic_id"],
        government=probe_row["government"],
        label=probe_row["label"],
        languages=languages,
    )


@router.post("/bias/back-translate", response_model=BackTranslateOut)
async def back_translate(body: BackTranslateIn) -> BackTranslateOut:
    if not body.text.strip():
        return BackTranslateOut(translated="")

    import openai

    from red_team_platform.config import get_settings

    settings = get_settings()
    lang_names = {"zh": "Chinese", "ru": "Russian", "ar": "Arabic"}
    client = openai.OpenAI(base_url=f"{settings.ollama_base_url}/v1", api_key="local")
    msg = client.chat.completions.create(
        model=settings.ollama_model,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Translate the following {lang_names[body.source_lang]} text to English."
                    f" Return only the translation, no explanation:\n\n{body.text}"
                ),
            }
        ],
    )
    translated = msg.choices[0].message.content or "" if msg.choices else ""
    return BackTranslateOut(translated=translated)
