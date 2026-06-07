from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from error_hide_seek.api.deps import get_db
from error_hide_seek.api.schemas import ExperimentResultsOut
from error_hide_seek.models import Experiment
from error_hide_seek.scoring.scorer import compute_experiment_results

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{experiment_id}", response_model=ExperimentResultsOut)
async def get_results(
    experiment_id: int, db: AsyncSession = Depends(get_db)
) -> ExperimentResultsOut:
    exp = await db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(404, "Experiment not found")
    return await compute_experiment_results(db, experiment_id)
