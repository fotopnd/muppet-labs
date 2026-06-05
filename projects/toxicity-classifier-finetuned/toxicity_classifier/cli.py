from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

_train_app = typer.Typer(add_completion=False)
_eval_app = typer.Typer(add_completion=False)


@_train_app.command()
def train_cmd(
    model: Annotated[str, typer.Option(help="Model to fine-tune: distilbert or roberta")],
    output_dir: Annotated[Path, typer.Option(help="Directory to save checkpoints")] = Path(
        "checkpoints"
    ),
    epochs: Annotated[int, typer.Option(help="Number of training epochs")] = 4,
    batch_size: Annotated[
        int | None, typer.Option(help="Per-device batch size (default: 32 distilbert, 16 roberta)")
    ] = None,
    lr: Annotated[
        float | None, typer.Option(help="Learning rate (default: 2e-5 distilbert, 1e-5 roberta)")
    ] = None,
    max_train_samples: Annotated[
        int | None, typer.Option(help="Cap training examples (useful for fast local iteration)")
    ] = None,
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    kwargs: dict = {}
    if batch_size is not None:
        kwargs["batch_size"] = batch_size
    if lr is not None:
        kwargs["lr"] = lr

    if model == "distilbert":
        from toxicity_classifier.train_distilbert import train
    elif model == "roberta":
        from toxicity_classifier.train_roberta import train
    elif model == "detoxify":
        from toxicity_classifier.train_detoxify import train
    else:
        typer.echo(f"Unknown model: {model!r}. Choose 'distilbert', 'roberta', or 'detoxify'.", err=True)
        raise typer.Exit(code=1)

    checkpoint = train(
        data_dir=_jigsaw_dir(),
        output_dir=output_dir,
        epochs=epochs,
        max_train_samples=max_train_samples,
        **kwargs,
    )
    typer.echo(f"Training complete. Checkpoint: {checkpoint}")


@_eval_app.command()
def evaluate_cmd(
    model: Annotated[str, typer.Option(help="Model to evaluate: distilbert or roberta")],
    checkpoint_dir: Annotated[Path, typer.Option(help="Path to saved checkpoint directory")],
    output_dir: Annotated[Path, typer.Option(help="Directory to write eval JSON")] = Path(
        "eval_results"
    ),
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if model not in ("distilbert", "roberta", "detoxify"):
        typer.echo(f"Unknown model: {model!r}. Choose 'distilbert', 'roberta', or 'detoxify'.", err=True)
        raise typer.Exit(code=1)

    if model == "detoxify":
        from toxicity_classifier.evaluate_detoxify import evaluate_detoxify
        evaluate_detoxify(
            checkpoint_dir=checkpoint_dir,
            data_dir=_jigsaw_dir(),
            output_dir=output_dir,
        )
    else:
        from toxicity_classifier.evaluate import evaluate
        evaluate(
            checkpoint_dir=checkpoint_dir,
            model_key=model,  # type: ignore[arg-type]
            data_dir=_jigsaw_dir(),
            output_dir=output_dir,
        )


def _jigsaw_dir() -> Path:
    from toxicity_classifier.config import Settings

    return Settings().jigsaw_data_dir


# Entry point wrappers — called by pyproject.toml [project.scripts]
def run_train() -> None:
    _train_app()


def run_evaluate() -> None:
    _eval_app()
