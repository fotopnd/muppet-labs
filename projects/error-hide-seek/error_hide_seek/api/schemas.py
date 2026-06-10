from datetime import datetime

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str
    description: str = ""
    paper_ids: list[int] = Field(..., min_length=1)


class SessionCreate(BaseModel):
    experiment_id: int
    paper_id: int


class DetectionIn(BaseModel):
    text_excerpt: str = Field(..., min_length=15)
    note: str | None = None


class ReviewSubmit(BaseModel):
    session_id: int
    detections: list[DetectionIn]


class PaperOut(BaseModel):
    id: int
    arxiv_id: str
    title: str
    abstract: str
    categories: str
    fetched_at: datetime

    model_config = {"from_attributes": True}


class PapersPageOut(BaseModel):
    items: list[PaperOut]
    total: int
    offset: int
    limit: int


class ExperimentPaperOut(BaseModel):
    paper_id: int
    title: str
    arxiv_id: str
    condition: str
    intended_category: str | None = None


class ExperimentSummaryOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    paper_count: int


class ExperimentOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime
    papers: list[ExperimentPaperOut]


class SessionListItemOut(BaseModel):
    session_id: int
    condition: str
    status: str


class AnnotationOut(BaseModel):
    id: int
    text_excerpt: str
    confidence: str
    reason: str


class AutoScoredResult(BaseModel):
    true_positives: int
    false_positives: int
    tpr: float
    fpr: float


class SessionOut(BaseModel):
    session_id: int
    experiment_id: int
    paper_id: int
    paper_title: str
    condition: str
    status: str
    abstract_text: str
    annotations: list[AnnotationOut]
    scored_result: AutoScoredResult | None
    agent_run_status: str | None = None
    parse_failures: int = 0


class ReviewConfirmOut(BaseModel):
    session_id: int
    status: str


class CategoryResultOut(BaseModel):
    category: str
    planted_count: int
    detected_count: int
    tpr: float | None


class ConditionResultOut(BaseModel):
    condition: str
    sessions_total: int
    sessions_complete: int
    true_positive_rate: float | None
    false_positive_rate: float | None
    by_category: list[CategoryResultOut]


class ExperimentResultsOut(BaseModel):
    experiment_id: int
    uplift: float | None
    conditions: list[ConditionResultOut]
