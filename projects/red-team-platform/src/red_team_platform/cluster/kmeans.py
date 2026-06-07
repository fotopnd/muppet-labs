from __future__ import annotations

import logging
from dataclasses import dataclass
from statistics import mode

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    cluster_id: int
    run_id: str
    attack_text: str
    harm_category: str
    strategy: str
    classifier_score: float


@dataclass
class ClusterSummaryResult:
    cluster_id: int
    size: int
    top_harm_category: str
    top_strategy: str
    representative_text: str


def cluster_failures(
    rows: list[dict],
    k: int,
) -> tuple[list[ClusterResult], list[ClusterSummaryResult]]:
    """
    Vectorises attack_text with TfidfVectorizer, clusters with KMeans.
    Pure function — no DB calls.
    Raises ValueError if len(rows) < k.
    """
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import euclidean_distances

    if len(rows) < k:
        raise ValueError(f"Not enough failures to cluster (need at least {k}, have {len(rows)})")

    texts = [r["attack_text"] for r in rows]
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
    X = vectorizer.fit_transform(texts)

    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(X)

    cluster_results: list[ClusterResult] = []
    summary_results: list[ClusterSummaryResult] = []

    for cid in range(k):
        mask = labels == cid
        cluster_indices = [i for i, m in enumerate(mask) if m]
        cluster_rows = [rows[i] for i in cluster_indices]

        if not cluster_rows:
            continue

        # Find representative: row closest to centroid
        centroid = kmeans.cluster_centers_[cid].reshape(1, -1)
        cluster_vectors = X[cluster_indices]
        distances = euclidean_distances(cluster_vectors, centroid).flatten()
        rep_idx = int(np.argmin(distances))
        representative_text = cluster_rows[rep_idx]["attack_text"]

        # Mode harm_category and strategy
        categories = [r["harm_category"] for r in cluster_rows]
        strategies = [r["strategy"] for r in cluster_rows]
        top_category = mode(categories)
        top_strategy = mode(strategies)

        for row in cluster_rows:
            cluster_results.append(
                ClusterResult(
                    cluster_id=cid,
                    run_id=str(row["run_id"]),
                    attack_text=row["attack_text"],
                    harm_category=row["harm_category"],
                    strategy=row["strategy"],
                    classifier_score=float(row["classifier_score"]),
                )
            )

        summary_results.append(
            ClusterSummaryResult(
                cluster_id=cid,
                size=len(cluster_rows),
                top_harm_category=top_category,
                top_strategy=top_strategy,
                representative_text=representative_text,
            )
        )

    return cluster_results, summary_results


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    from sqlalchemy import create_engine, delete, select
    from sqlalchemy.orm import Session

    from red_team_platform.config import get_settings
    from red_team_platform.models import Attack, ClusterSummary, FailureCluster, Run

    settings = get_settings()
    k = settings.cluster_k

    engine = create_engine(settings.sync_database_url, pool_pre_ping=True)

    with Session(engine) as session:
        # Query all successful runs joined to attacks
        stmt = (
            select(
                Run.id.label("run_id"),
                Attack.attack_text,
                Attack.harm_category,
                Attack.strategy,
                Run.classifier_score,
            )
            .join(Attack, Run.attack_id == Attack.id)
            .where(Run.jailbreak_success == True)  # noqa: E712
        )
        result = session.execute(stmt)
        rows = [row._asdict() for row in result]

    if len(rows) < k:
        print(
            f"Not enough failures to cluster (need at least {k}, have {len(rows)}). "
            "Run more attack sessions first."
        )
        return

    logger.info("Clustering %d successful attacks into %d clusters...", len(rows), k)
    cluster_results, summary_results = cluster_failures(rows, k)

    with Session(engine) as session:
        session.execute(delete(FailureCluster))
        session.execute(delete(ClusterSummary))

        for r in cluster_results:
            import uuid

            session.add(
                FailureCluster(
                    cluster_id=r.cluster_id,
                    run_id=uuid.UUID(r.run_id),
                )
            )

        for s in summary_results:
            session.add(
                ClusterSummary(
                    cluster_id=s.cluster_id,
                    size=s.size,
                    top_harm_category=s.top_harm_category,
                    top_strategy=s.top_strategy,
                    representative_text=s.representative_text,
                )
            )

        session.commit()

    print(f"\n{'Cluster':>8} {'Size':>6} {'Top Category':<40} {'Top Strategy':<25} Representative")
    print("-" * 120)
    for s in sorted(summary_results, key=lambda x: x.size, reverse=True):
        rep = s.representative_text[:60].replace("\n", " ")
        cat = s.top_harm_category
        strat = s.top_strategy
        print(f"{s.cluster_id:>8} {s.size:>6} {cat:<40} {strat:<25} {rep}...")
    print(f"\nClustering complete. {len(summary_results)} clusters written to DB.")
