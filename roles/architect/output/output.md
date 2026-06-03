# Architect Output — toxicity-classifier-finetuned

**Role:** architect
**Sequence:** `new-project-full` (step 3)
**Date:** 2026-06-03

---

## Planner Open Questions — Resolved

**Q1 — Training loop: `Trainer` vs manual loop.**
Accepted: `Trainer`-based with inline comments. Each `TrainingArguments` field that is non-default gets a one-line comment explaining why. No `train_manual.py`.

**Q2 — MPS + bf16.**
Accepted: fp32 on MPS, bf16 on CUDA only. `get_device()` returns a `DeviceConfig(device, use_bf16)` dataclass. `TrainingArguments` receives `bf16=device_config.use_bf16`.

**Q3 — `--max-train-samples`.**
Accepted: exposed on both training CLIs, default `None` (full dataset). When set, the train split is truncated before tokenisation using `dataset.select(range(n))`.

**Q4 — Zero-shot baseline checkpoints.**
Cross-checked against project 22 consumers:
- DistilBERT zero-shot: `typeform/distilbert-base-uncased-mnli` via `pipeline("zero-shot-classification")`
- RoBERTa zero-shot: `roberta-large-mnli` via `pipeline("zero-shot-classification")`

These are NLI models, not sequence classifiers — their inference interface differs from the fine-tuned models. The evaluate module runs both the zero-shot pipeline (candidate labels: `["toxic content", "safe content"]`, threshold 0.5 on `"toxic content"` score) and the fine-tuned classifier on the same test set, then computes metrics for both. The comparison is apples-to-apples on the Jigsaw test split.

---

## System Overview

The project is a single Python package (`toxicity_classifier`) with two CLI entry points (`train`, `evaluate`) and a supporting Colab notebook. The `data` module owns all dataset I/O and tokenisation. The two training modules (`train_distilbert`, `train_roberta`) each define a `train()` function that accepts a config object and runs a HuggingFace `Trainer` loop, saving the best checkpoint by validation F1. The `evaluate` module defines an `evaluate()` function that loads a saved checkpoint, optionally loads the matching zero-shot pipeline for baseline comparison, and writes a structured JSON result file. The `cli` module wires both entry points via Typer. `config.py` and `device.py` are shared utilities with no upstream dependencies within the package.

---

## Data Models

```python
# device.py
@dataclass
class DeviceConfig:
    device: torch.device       # MPS | CUDA | CPU
    use_bf16: bool             # True only when device.type == "cuda"

# data.py — internal, not exported
@dataclass
class DataSplits:
    train: datasets.Dataset    # tokenised, columns: input_ids, attention_mask, labels
    val: datasets.Dataset
    test: datasets.Dataset     # held out; only evaluate() touches this
    label_columns: list[str]   # ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]
                               # retained in test split for per-category eval; not used in training

# evaluate.py
@dataclass
class ModelMetrics:
    f1: float
    precision: float
    recall: float
    auc_roc: float
    per_category: dict[str, float]   # category name → accuracy vs binary prediction

@dataclass
class EvalResult:
    model_slug: str            # e.g. "distilbert-finetuned" or "distilbert-zero-shot"
    checkpoint_dir: str | None # None for zero-shot baseline
    finetuned: ModelMetrics
    zero_shot_baseline: ModelMetrics
    evaluated_at: str          # ISO 8601 UTC timestamp
    test_size: int
```

---

## Module Interfaces

### `config.py`
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    jigsaw_data_dir: Path           # directory containing train.csv
    model_output_dir: Path = Path("checkpoints")
```

### `device.py`
```python
def get_device() -> DeviceConfig:
    # Returns MPS if torch.backends.mps.is_available(),
    # CUDA if torch.cuda.is_available(), else CPU.
    # Sets use_bf16=True only for CUDA.
    ...
```

### `data.py`
```python
def load_jigsaw(data_dir: Path) -> pd.DataFrame:
    # Reads train.csv. Validates required columns exist.
    # Raises FileNotFoundError with path if CSV missing.
    # Raises ValueError if required columns absent.
    ...

def get_splits(
    df: pd.DataFrame,
    seed: int = 42,
    max_train_samples: int | None = None,
) -> DataSplits:
    # Stratified 80/10/10 split on the binary `toxic` column.
    # If max_train_samples is set, truncates train split after splitting.
    # Returns DataSplits with raw (un-tokenised) text + label columns.
    ...

def tokenise_splits(
    splits: DataSplits,
    tokenizer: PreTrainedTokenizerBase,
    max_length: int = 128,
) -> DataSplits:
    # Applies tokenizer to train, val, test.
    # Sets format to torch tensors.
    # Preserves label_columns in test split (needed by evaluate.py).
    ...
```

### `train_distilbert.py`
```python
BASE_CHECKPOINT = "distilbert-base-uncased"

def train(
    data_dir: Path,
    output_dir: Path,
    epochs: int = 4,
    batch_size: int = 32,
    lr: float = 2e-5,
    max_train_samples: int | None = None,
) -> Path:
    # Returns path to best checkpoint directory.
    # Uses HuggingFace Trainer with compute_metrics returning {"f1": float}.
    # TrainingArguments: load_best_model_at_end=True, metric_for_best_model="f1",
    #   greater_is_better=True, evaluation_strategy="epoch", save_strategy="epoch",
    #   bf16=device_config.use_bf16, no_cuda=(device_config.device.type != "cuda").
    # Saves training log to output_dir / "train_log.json".
    ...
```

### `train_roberta.py`
```python
BASE_CHECKPOINT = "roberta-base"

def train(
    data_dir: Path,
    output_dir: Path,
    epochs: int = 4,
    batch_size: int = 16,   # roberta-base needs smaller batch than distilbert on MPS
    lr: float = 1e-5,
    max_train_samples: int | None = None,
) -> Path:
    # Same structure as train_distilbert.train().
    # Default batch size is 16 (roberta-base is larger; 32 will OOM on 8GB MPS).
    ...
```

### `evaluate.py`
```python
ZERO_SHOT_CHECKPOINTS: dict[str, str] = {
    "distilbert": "typeform/distilbert-base-uncased-mnli",
    "roberta": "roberta-large-mnli",
}
ZERO_SHOT_CANDIDATE_LABELS = ["toxic content", "safe content"]
ZERO_SHOT_TOXIC_LABEL = "toxic content"
ZERO_SHOT_THRESHOLD = 0.5

def evaluate(
    checkpoint_dir: Path,
    model_key: Literal["distilbert", "roberta"],
    data_dir: Path,
    output_dir: Path = Path("eval_results"),
) -> EvalResult:
    # 1. Load fine-tuned model from checkpoint_dir.
    # 2. Load zero-shot pipeline for model_key from ZERO_SHOT_CHECKPOINTS.
    # 3. Run both on test split. Collect binary predictions.
    # 4. Compute ModelMetrics for each. Per-category accuracy:
    #    for each category col c in label_columns,
    #    accuracy = mean(prediction == df[c]) where df[c] in {0,1}.
    # 5. Write EvalResult as JSON to output_dir / f"{model_key}-finetuned-{timestamp}.json".
    # 6. Print summary table to stdout.
    # Returns EvalResult.
    ...

def _predict_finetuned(
    model: AutoModelForSequenceClassification,
    tokenizer: PreTrainedTokenizerBase,
    texts: list[str],
    device: torch.device,
    batch_size: int = 64,
) -> list[int]:
    # Runs batched inference. Returns list of 0/1 predictions.
    ...

def _predict_zero_shot(
    pipeline_obj: Pipeline,
    texts: list[str],
) -> list[int]:
    # Runs zero-shot pipeline. Threshold on ZERO_SHOT_TOXIC_LABEL score.
    ...

def _compute_metrics(
    predictions: list[int],
    labels: list[int],
    category_arrays: dict[str, list[int]],
) -> ModelMetrics:
    ...
```

### `cli.py`
```python
app = typer.Typer()

@app.command("train")
def train_cmd(
    model: Annotated[str, typer.Option(help="distilbert or roberta")],
    output_dir: Annotated[Path, typer.Option()] = Path("checkpoints"),
    epochs: Annotated[int, typer.Option()] = 4,
    batch_size: Annotated[int | None, typer.Option()] = None,  # None → model default
    lr: Annotated[float | None, typer.Option()] = None,        # None → model default
    max_train_samples: Annotated[int | None, typer.Option()] = None,
) -> None: ...

@app.command("evaluate")
def evaluate_cmd(
    model: Annotated[str, typer.Option(help="distilbert or roberta")],
    checkpoint_dir: Annotated[Path, typer.Option()],
    output_dir: Annotated[Path, typer.Option()] = Path("eval_results"),
) -> None: ...

# pyproject.toml [project.scripts]:
# train = "toxicity_classifier.cli:train_cmd"
# evaluate = "toxicity_classifier.cli:evaluate_cmd"
```

---

## Dependencies

```
cli.py
  → train_distilbert.py, train_roberta.py   (via model dispatch)
  → evaluate.py

train_distilbert.py
  → data.py
  → device.py
  → config.py

train_roberta.py
  → data.py
  → device.py
  → config.py

evaluate.py
  → data.py       (test split only)
  → device.py
  → config.py

data.py
  → config.py     (Settings.jigsaw_data_dir)

device.py         (no internal deps)
config.py         (no internal deps)
```

No circular dependencies. `data.py` is the only module with a HuggingFace `datasets` import at module level — all `transformers` imports are deferred inside function bodies to avoid penalising CLI startup.

---

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | Specific exceptions with context: `FileNotFoundError(f"Jigsaw CSV not found at {path}")`, `ValueError(f"Missing columns: {missing}")`. No broad `Exception` catches outside CLI top-level. |
| Configuration | `Settings` loaded once in CLI entry points and passed as arguments. Training modules accept `data_dir`/`output_dir` as `Path` — no global config access inside modules. |
| Logging | `logging` stdlib. `basicConfig(level=INFO)` in CLI entry points. Training modules use `logger = logging.getLogger(__name__)`. HuggingFace `Trainer` logging set to `transformers.logging.set_verbosity_info()` in training modules. |
| Testing | Unit tests only — no live model downloads. `mock_model_factory` fixture in `conftest.py` returns a randomly-initialised `AutoModelForSequenceClassification` sized to match the real architecture config (DistilBERT: `hidden_size=768, num_hidden_layers=6`; RoBERTa: `hidden_size=768, num_hidden_layers=12`). Forward pass shape and loss values are verified, not weights. |

---

## Implementation Notes for Implementer

1. **`datasets` import deferral:** `data.py` uses `from datasets import Dataset` inside `get_splits()` and `tokenise_splits()`, not at module level. This keeps `uv run evaluate --help` fast even when HuggingFace cache is cold.

2. **Stratified split:** Use `sklearn.model_selection.train_test_split` with `stratify=df["toxic"]` — the `datasets` library's `.train_test_split()` does not support stratification.

3. **Label retention in test split:** After tokenisation, `label_columns` data is attached to the test `Dataset` as additional columns (`toxic`, `severe_toxic`, etc. as integer columns). `tokenize_splits()` must not drop them. The `Trainer` ignores extra columns during training but `evaluate.py` needs them for per-category metrics.

4. **`load_best_model_at_end` requires `save_strategy == evaluation_strategy`:** Both must be `"epoch"`. If they differ, HuggingFace raises a config error at `Trainer.__init__`. Set both explicitly.

5. **MPS memory:** `roberta-base` with batch size 32 on MPS 8GB will OOM. Default batch size for RoBERTa is 16. The CLI accepts `--batch-size` override — document in README that 8GB MPS should use ≤16 for RoBERTa.

6. **Zero-shot pipeline in evaluate.py:** `pipeline("zero-shot-classification", device=-1)` forces CPU. Do not pass the MPS device to the zero-shot pipeline — MPS support for zero-shot classification pipelines is inconsistent across `transformers` versions; CPU is reliable and fast enough for a one-pass evaluation.

7. **Checkpoint directory naming:** `output_dir / "distilbert-best"` and `output_dir / "roberta-best"` for the checkpoints that project 22 loads. The `Trainer` saves intermediate checkpoints as `checkpoint-<step>` — the implementer must copy (or `save_pretrained`) to the named directory after training completes.

8. **`train_log.json` format:**
   ```json
   [
     {"epoch": 1, "train_loss": 0.42, "val_loss": 0.38, "val_f1": 0.81},
     ...
   ]
   ```
   Written by a custom `TrainerCallback` that appends to a list after each epoch's evaluation.

9. **`EvalResult` JSON serialisation:** `dataclasses.asdict()` produces a plain dict. Write with `json.dumps(result_dict, indent=2)`. The `evaluated_at` field is `datetime.now(UTC).isoformat()`.

10. **Test mock strategy:** In `test_train.py`, mock `AutoModelForSequenceClassification.from_pretrained` to return a real but randomly-initialised model (use `AutoConfig` + `AutoModelForSequenceClassification(config)` with a minimal config). Run a single training step with a 4-row mock dataset — assert loss is a finite float, checkpoint dir is created.

---

## Handoff

**Next role:** implementer
**What the implementer does with this:**
- Follow `skills/setup-uv-project.md` to initialise `projects/toxicity-classifier-finetuned/` with uv.
- Implement all modules per the interfaces above, in dependency order: `config.py` → `device.py` → `data.py` → `train_distilbert.py` + `train_roberta.py` → `evaluate.py` → `cli.py`.
- Write all tests. Run `uv run pytest` and `uv run ruff check .` before declaring done.
- Write `README.md` covering: Kaggle dataset download, training commands with expected MPS runtimes, evaluation commands, Colab notebook usage, and how to set `distilbert_checkpoint_path` / `roberta_checkpoint_path` in project 22's `.env`.
- Write `notebooks/colab_training.ipynb` with cells mirroring the training CLI flow: pip install, mount Drive, set paths, call `train()` directly.

**Flags for implementer:**
- Implementation note 3 (label retention in test split) is easy to miss — verify that `label_columns` survive `tokenise_splits()` before writing `evaluate.py`.
- Implementation note 7 (checkpoint directory naming) is required for project 22 compatibility — the final checkpoint must be saved as `distilbert-best` / `roberta-best`, not as a `checkpoint-<step>` subdirectory.
- Implementation note 4 (`load_best_model_at_end` + `save_strategy`) will raise a runtime error if misconfigured — set both to `"epoch"` explicitly.
