from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.api.deps import get_db
from red_team_platform.api.schemas import (
    ClusterMemberOut,
    ClusterMembersOut,
    ClustersOut,
    ClusterSummaryOut,
)
from red_team_platform.models import Attack, ClusterSummary, FailureCluster, Run

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=ClustersOut)
async def list_clusters(db: AsyncSession = Depends(get_db)) -> ClustersOut:
    result = await db.execute(select(ClusterSummary).order_by(ClusterSummary.size.desc()))
    summaries = result.scalars().all()
    return ClustersOut(summaries=[ClusterSummaryOut.model_validate(s) for s in summaries])


@router.get("/{cluster_id}/members", response_model=ClusterMembersOut)
async def get_cluster_members(
    cluster_id: int, db: AsyncSession = Depends(get_db)
) -> ClusterMembersOut:
    # Verify cluster exists
    summary_result = await db.execute(
        select(ClusterSummary).where(ClusterSummary.cluster_id == cluster_id)
    )
    if summary_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    result = await db.execute(
        select(
            FailureCluster.cluster_id,
            FailureCluster.run_id,
            Attack.attack_text,
            Attack.harm_category,
            Attack.strategy,
            Run.classifier_score,
            Run.jailbreak_success,
            Run.latency_ms,
            Run.model_name,
        )
        .join(Run, FailureCluster.run_id == Run.id)
        .join(Attack, Run.attack_id == Attack.id)
        .where(FailureCluster.cluster_id == cluster_id)
        .order_by(Run.classifier_score.desc())
    )

    members = [
        ClusterMemberOut(
            run_id=row.run_id,
            cluster_id=row.cluster_id,
            attack_text=row.attack_text,
            harm_category=row.harm_category,
            strategy=row.strategy,
            classifier_score=row.classifier_score,
            jailbreak_success=row.jailbreak_success,
            latency_ms=row.latency_ms,
            model_name=row.model_name,
        )
        for row in result
    ]
    return ClusterMembersOut(cluster_id=cluster_id, members=members)
