# Reviewer Output — toxicity-classifier-finetuned

**Role:** reviewer
**Sequence:** `new-project-full` (step 8)
**Date:** 2026-06-03

---

## Summary

The implementation is functionally correct and convention-compliant. The only significant finding is a structural fragility in `evaluate.py`: the test set is reconstructed via a private `_get_raw_test()` function that duplicates part of `get_splits()`, creating two separate code paths that must stay in sync to avoid silent label misalignment. This is not currently broken — both paths use identical parameters — but it is the most likely place to introduce a bug in a future change. One test gap (train log file not verified) and three minor style issues are also noted. Recommended next action: apply the three fixes below before proceeding to retro.

---

## Correctness

**1. `evaluate.py:70-74` — Two-path test set reconstruction (WARNING)**

`evaluate()` calls `tokenise_splits(get_splits(df))` to produce `test_ds` (for `true_labels` and category arrays), then independently calls `_get_raw_test(df)` (for `raw_texts`). Both derive the test split using `test_size=0.10, random_state=42, stratify=df["toxic"]` — so the row set and order are currently consistent.

The fragility: if `get_splits()` ever changes its first split parameters (seed, test size, or stratify), `_get_raw_test()` will silently produce a different test set, aligning predictions against wrong labels. There is no runtime check that the two sets are the same size or contain the same rows.

Fix: remove `_get_raw_test()` entirely. In `get_splits()`, retain raw text in the `DataSplits.test` dataset alongside tokenized tensors (the `comment_text` column is already there before `tokenise_splits` is called). In `evaluate()`, use `test_df = test_ds.to_pandas()["comment_text"].tolist()` to recover raw texts from the single authoritative test split. This eliminates the duplicate code path.

Severity: **warning** — not currently broken, but fragile enough to flag before the codebase has users.

---

**2. `evaluate.py:115-120` — `_get_raw_test` return type untyped and return value partially unused (MINOR)**

```python
def _get_raw_test(df) -> tuple:
    ...
    return train_val, None, test
```

`df` has no type annotation (should be `pd.DataFrame`). Return type should be `tuple[pd.DataFrame, None, pd.DataFrame]`. `train_val` is returned but never used by the caller (which unpacks `_, _, test_df = _get_raw_test(df)`). If the fix in Finding 1 is applied, this function is removed entirely; if not, annotate it properly.

Severity: **minor**.

---

**3. `evaluate.py:123-128` — `_predict_finetuned` parameters untyped (MINOR)**

```python
def _predict_finetuned(
    model,
    tokenizer,
    texts: list[str],
    device: torch.device,
    ...
```

`model` and `tokenizer` have no type annotations. Per python-conventions.md, all function parameters must be typed. The correct types are `AutoModelForSequenceClassification` (from `transformers`) and `PreTrainedTokenizerBase`. These can be imported at module level since `evaluate.py` already imports `torch` at module level — the deferred-import pattern applies only to slow imports (`transformers` model loading); the base classes are lightweight.

Severity: **minor**.

---

**4. `cli.py:32` — `kwargs: dict` untyped (MINOR)**

```python
kwargs: dict = {}
```

Should be `dict[str, int | float]`. Not a correctness issue.

Severity: **minor**.

---

## Style

**S1. `data.py:22-25` — `DataSplits` fields typed as `object` (NOTE)**

The comment correctly explains this is intentional (deferred import). This is a known, documented tradeoff per the implementer notes. No action required; noting for completeness.

**S2. `pyproject.toml` — `asyncio_mode = "auto"` is unused (NOTE)**

No async tests exist in the project. `asyncio_mode = "auto"` is a leftover from the workspace uv template. Remove it to avoid confusion.

---

## Tests

**T1. Train log file not verified (MINOR GAP)**

`test_train_distilbert_creates_checkpoint` and `test_train_roberta_creates_checkpoint` assert the checkpoint directory and `config.json` exist, but do not verify that `distilbert-train-log.json` / `roberta-train-log.json` are written. The log file is important for the experiment document. Add:

```python
assert (tmp_path / "out" / "distilbert-train-log.json").exists()
```

**T2. `mock_tokenizer` is DistilBERT for all tests including RoBERTa (NOTE)**

`test_train_roberta_creates_checkpoint` uses the DistilBERT tokenizer (from `mock_tokenizer` fixture) with the RoBERTa-shaped model. This works for the checkpoint-creation test but does not exercise RoBERTa tokenization. For a portfolio build, acceptable — the tokenization logic is in HuggingFace, not this project.

**T3. No test for CLI entry points (NOTE)**

`run_train()` and `run_evaluate()` are not directly tested. Typer CLI smoke tests (via `CliRunner` or just `--help`) are a reasonable addition for portfolio completeness but not blocking.

---

## Refactor Candidates

**R1. `_get_raw_test()` — redundant with `get_splits()` (follows from Finding 1)**

See Finding 1 above. Removing this function and reading raw texts directly from `test_ds` is the cleanest fix.

**R2. `EpochLogCallback` defined inside `train()` (LOW PRIORITY)**

The callback class captures `log_entries` via closure, which works correctly. Extracting it to module level with an explicit list argument would make it independently testable. Low priority for a training script.

**R3. `train_distilbert.py` and `train_roberta.py` share ~80% of their `train()` body**

A `_run_training(base_checkpoint, default_batch_size, ...)` shared function could reduce duplication. Deferred — the current duplication is explicit and clear, and refactoring would complicate the deferred-import pattern.

---

## Verdict

**PASS WITH NOTES**

No blocking correctness issues. Three fixes recommended before retro:
1. Remove `_get_raw_test()` and derive raw texts from `test_ds` directly (Finding 1)
2. Type-annotate `_predict_finetuned` model and tokenizer parameters (Finding 3)
3. Remove `asyncio_mode = "auto"` from `pyproject.toml` (Style S2)

The train log test gap (T1) is also worth closing in the same pass.

---

## Handoff

**Next role:** retro (after human sign-off and implementer applies the four fixes above)

**Fixes to apply (implementer pass):**
1. `evaluate.py` — remove `_get_raw_test()`; derive `raw_texts` from `test_ds` via `.to_pandas()["comment_text"].tolist()`; update `_get_raw_test` callers accordingly
2. `evaluate.py` — add type annotations to `_predict_finetuned` (`model: AutoModelForSequenceClassification`, `tokenizer: PreTrainedTokenizerBase`) with module-level imports
3. `pyproject.toml` — remove `asyncio_mode = "auto"` from `[tool.pytest.ini_options]`
4. `tests/test_train.py` — add assertion that train log JSON file exists after `test_train_distilbert_creates_checkpoint` and `test_train_roberta_creates_checkpoint`
