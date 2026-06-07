from collections import defaultdict

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.schemas import (
    CategoryResultOut,
    ConditionResultOut,
    ExperimentResultsOut,
)
from error_hide_seek.models import (
    Condition,
    HumanDetection,
    PlantedError,
    ReviewSession,
    SessionStatus,
)


def is_true_positive(detection_excerpt: str, planted_original: str) -> bool:
    d = detection_excerpt.lower().strip()
    p = planted_original.lower().strip()
    return d in p or p in d


def score_detections(
    detections: list[str],
    planted_original: str,
) -> tuple[bool, int]:
    planted_detected = any(is_true_positive(d, planted_original) for d in detections)
    false_positive_count = sum(1 for d in detections if not is_true_positive(d, planted_original))
    return planted_detected, false_positive_count


async def compute_experiment_results(
    session: AsyncSession,
    experiment_id: int,
) -> ExperimentResultsOut:
    # First completed session per (paper_id, condition)
    first_completed_subq = (
        select(
            ReviewSession.id,
            ReviewSession.paper_id,
            ReviewSession.condition,
        )
        .where(
            ReviewSession.experiment_id == experiment_id,
            ReviewSession.status == SessionStatus.COMPLETED,
        )
        .distinct(ReviewSession.paper_id, ReviewSession.condition)
        .order_by(
            ReviewSession.paper_id,
            ReviewSession.condition,
            ReviewSession.completed_at.asc(),
        )
        .subquery()
    )

    # Load those sessions with planted error categories
    session_rows = (
        await session.execute(
            select(
                first_completed_subq.c.id,
                first_completed_subq.c.paper_id,
                first_completed_subq.c.condition,
                PlantedError.category,
                PlantedError.original_text,
            ).join(
                PlantedError,
                sa.and_(
                    PlantedError.paper_id == first_completed_subq.c.paper_id,
                    PlantedError.experiment_id == experiment_id,
                ),
            )
        )
    ).all()

    # Load human detections for those session ids
    session_ids = [r.id for r in session_rows]
    detections_rows: list = []
    if session_ids:
        detections_rows = (
            (
                await session.execute(
                    select(HumanDetection).where(HumanDetection.review_session_id.in_(session_ids))
                )
            )
            .scalars()
            .all()
        )

    det_by_session: dict[int, list[HumanDetection]] = defaultdict(list)
    for d in detections_rows:
        det_by_session[d.review_session_id].append(d)

    # Aggregate per condition
    condition_data: dict[str, dict] = {
        c.value: {"sessions": [], "category_sessions": defaultdict(list)} for c in Condition
    }

    for row in session_rows:
        cond = row.condition
        dets = det_by_session[row.id]
        tp_found = any(d.is_true_positive for d in dets)
        fp_count = sum(1 for d in dets if d.is_true_positive is False)
        total_dets = len(dets)
        condition_data[cond]["sessions"].append(
            {"tp": tp_found, "fp": fp_count, "total_dets": total_dets}
        )
        condition_data[cond]["category_sessions"][row.category].append({"tp": tp_found})

    # Build total sessions count (all sessions, including open)
    total_counts_rows = (
        await session.execute(
            select(
                ReviewSession.condition,
                func.count(ReviewSession.id).label("total"),
                func.count(ReviewSession.completed_at).label("complete"),
            )
            .where(ReviewSession.experiment_id == experiment_id)
            .group_by(ReviewSession.condition)
        )
    ).all()
    total_by_cond: dict[str, dict] = {}
    for r in total_counts_rows:
        total_by_cond[r.condition] = {"total": r.total, "complete": r.complete}

    condition_results: list[ConditionResultOut] = []
    tpr_by_condition: dict[str, float | None] = {}

    for cond in Condition:
        cval = cond.value
        agg = condition_data[cval]["sessions"]
        cat_agg = condition_data[cval]["category_sessions"]
        counts = total_by_cond.get(cval, {"total": 0, "complete": 0})

        if agg:
            detected = sum(1 for s in agg if s["tp"])
            planted_count = len(agg)
            tpr: float | None = detected / planted_count
            total_dets = sum(s["total_dets"] for s in agg)
            total_fp = sum(s["fp"] for s in agg)
            fpr: float | None = total_fp / total_dets if total_dets > 0 else 0.0
        else:
            tpr = None
            fpr = None
            planted_count = 0

        tpr_by_condition[cval] = tpr

        by_category: list[CategoryResultOut] = []
        for cat, cat_sessions in cat_agg.items():
            cat_detected = sum(1 for s in cat_sessions if s["tp"])
            cat_planted = len(cat_sessions)
            by_category.append(
                CategoryResultOut(
                    category=cat,
                    planted_count=cat_planted,
                    detected_count=cat_detected,
                    tpr=cat_detected / cat_planted if cat_planted > 0 else None,
                )
            )

        condition_results.append(
            ConditionResultOut(
                condition=cval,
                sessions_total=counts["total"],
                sessions_complete=counts["complete"],
                true_positive_rate=tpr,
                false_positive_rate=fpr,
                by_category=by_category,
            )
        )

    human_agent_tpr = tpr_by_condition.get(Condition.HUMAN_AGENT)
    unaided_tpr = tpr_by_condition.get(Condition.UNAIDED)
    uplift: float | None = (
        round(human_agent_tpr - unaided_tpr, 4)
        if human_agent_tpr is not None and unaided_tpr is not None
        else None
    )

    return ExperimentResultsOut(
        experiment_id=experiment_id,
        uplift=uplift,
        conditions=condition_results,
    )


def score_cli() -> None:
    import argparse

    import sqlalchemy as _sa
    from sqlalchemy.orm import Session as SyncSession

    parser = argparse.ArgumentParser(description="Print experiment results to stdout")
    parser.add_argument("--experiment-id", type=int, required=True)
    args = parser.parse_args()

    from error_hide_seek.config import settings as _settings

    engine = _sa.create_engine(_settings.sync_database_url)
    with SyncSession(engine) as sync_session:
        # Run sync query to fetch summary
        rows = sync_session.execute(
            sa.text(
                """
                SELECT rs.condition,
                       count(*) filter (where rs.status = 'completed') as complete,
                       count(*) as total,
                       count(*) filter (
                           where rs.status = 'completed'
                           and exists (
                               select 1 from human_detections hd
                               where hd.review_session_id = rs.id and hd.is_true_positive = true
                           )
                       ) as tp_sessions
                FROM review_sessions rs
                WHERE rs.experiment_id = :eid
                GROUP BY rs.condition
                """
            ),
            {"eid": args.experiment_id},
        ).all()

    print(f"\n## Experiment {args.experiment_id} Results\n")
    print("| Condition | Complete | Total | TPR |")
    print("|-----------|----------|-------|-----|")
    tpr_by: dict[str, float | None] = {}
    for r in rows:
        tpr = r.tp_sessions / r.complete if r.complete > 0 else None
        tpr_by[r.condition] = tpr
        tpr_str = f"{tpr:.1%}" if tpr is not None else "—"
        print(f"| {r.condition} | {r.complete} | {r.total} | {tpr_str} |")

    ha = tpr_by.get("human_agent")
    un = tpr_by.get("unaided")
    if ha is not None and un is not None:
        uplift = ha - un
        sign = "+" if uplift >= 0 else ""
        print(f"\n**Human Uplift:** {sign}{uplift:.1%}")
    else:
        print("\n**Human Uplift:** Results incomplete")
