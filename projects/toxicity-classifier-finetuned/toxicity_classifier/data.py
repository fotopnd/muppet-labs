from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

LABEL_COLUMNS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
REQUIRED_COLUMNS = {
    "comment_text",
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
}


@dataclass
class DataSplits:
    train: object  # datasets.Dataset — typed as object to defer import
    val: object
    test: object
    label_columns: list[str]


def load_jigsaw(data_dir: Path) -> pd.DataFrame:
    csv_path = data_dir / "train.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Jigsaw CSV not found at {csv_path}. "
            "Download from https://www.kaggle.com/c/jigsaw-toxic-comment-classification-challenge"
        )
    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Jigsaw CSV is missing required columns: {missing}")
    return df


def get_splits(
    df: pd.DataFrame,
    seed: int = 42,
    max_train_samples: int | None = None,
) -> DataSplits:
    from sklearn.model_selection import train_test_split

    # Stratified 80/10/10 split on binary toxic label
    train_val, test = train_test_split(df, test_size=0.10, random_state=seed, stratify=df["toxic"])
    # val is 10% of total = ~11.1% of the train_val remainder
    train, val = train_test_split(
        train_val, test_size=0.1111, random_state=seed, stratify=train_val["toxic"]
    )

    if max_train_samples is not None:
        train = train.iloc[:max_train_samples]

    train = train.reset_index(drop=True)
    val = val.reset_index(drop=True)
    test = test.reset_index(drop=True)

    import datasets as hf_datasets

    train_ds = hf_datasets.Dataset.from_pandas(train[["comment_text", "toxic"]])
    val_ds = hf_datasets.Dataset.from_pandas(val[["comment_text", "toxic"]])
    # Keep all label columns in test split for per-category evaluation
    test_ds = hf_datasets.Dataset.from_pandas(test[["comment_text"] + LABEL_COLUMNS])

    return DataSplits(train=train_ds, val=val_ds, test=test_ds, label_columns=LABEL_COLUMNS)


def tokenise_splits(
    splits: DataSplits,
    tokenizer: object,
    max_length: int = 128,
) -> DataSplits:
    def _tokenise(batch: dict) -> dict:
        return tokenizer(
            batch["comment_text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )

    train = splits.train.map(_tokenise, batched=True)
    val = splits.val.map(_tokenise, batched=True)
    # Tokenise test but preserve label columns — Trainer ignores extra columns
    test = splits.test.map(_tokenise, batched=True)

    # Rename toxic → labels so HuggingFace Trainer picks it up automatically
    train = train.rename_column("toxic", "labels")
    val = val.rename_column("toxic", "labels")
    # test keeps both: labels (for metric computation) and category columns (for per-category eval)
    test = test.rename_column("toxic", "labels")

    train.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
    val.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
    # test uses torch for the model columns but retains category columns as plain Python ints
    test.set_format(
        "torch",
        columns=["input_ids", "attention_mask", "labels"],
        output_all_columns=True,
    )

    return DataSplits(train=train, val=val, test=test, label_columns=splits.label_columns)
