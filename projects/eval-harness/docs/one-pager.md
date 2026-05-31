# Knowing Whether Your Model Is Still Behaving

Most teams building with large language models (LLMs) run a prompt, read the output, and decide whether it looks right. That works once. It stops working the moment the model is swapped, the prompt is adjusted, or a new model version is deployed, because there is no recorded baseline to compare against. The behavior drifted, and the first sign was a user report.

eval-harness was built to close that gap: a lightweight Python command-line interface (CLI) that runs structured test suites against local or cloud-hosted LLMs, scores each response against defined rubrics, persists all results to a SQLite database, and computes metric drift between any two runs.

## Background

Evaluating LLM behavior is a well-understood problem at scale, but the existing tools (Eleuther's `lm-evaluation-harness`, OpenAI evals, Weights and Biases Prompts) are built for production infrastructure teams. They assume cloud storage, CI pipelines, and dedicated evaluation clusters. For individual practitioners, researchers running local models, or early-stage projects, that overhead is the barrier, not the solution.

The practical question is narrower: when the model changes or the prompt changes, did the behavior change in a way that matters? Answering that question requires only three things: a deterministic way to run prompts, a consistent scoring method, and a record of previous results to compare against. eval-harness is those three things and nothing more.

## The Approach

The harness is built around four CLI commands: `run`, `diff`, `add-case`, and `list`. Each command is narrow in scope; together, they cover the full evaluation workflow.

`eval run` executes a test suite against a configured model, scores each response immediately after it is returned, and writes every result to SQLite. Temperature is fixed at 0.0 throughout, which makes runs deterministic and therefore comparable. Scoring operates in two modes: heuristic-only (keyword and pattern matching, no network access required) and LLM-as-judge (Claude evaluates each response against a rubric criterion, one criterion at a time). When both modes are active, the harness merges scores by a simple rule: if a heuristic score is available, it wins; if not, the judge score is used; the result is `None` only when both fail to produce a score.

`eval diff` computes metric drift between two run IDs. It calculates per-dataset pass rate deltas, refusal accuracy (defined as the fraction of cases where the model's refusal behavior matched the expected behavior, whether refusal or response), and flip counts (cases that changed from pass to fail or fail to pass between runs). Cases that appear in only one run are counted separately and excluded from flip detection, which avoids false positives when test suites evolve between runs.

Test cases come from three sources: the custom dataset (YAML files the operator authors directly), TruthfulQA (a standard benchmark for factual accuracy, loaded from HuggingFace), and AdvBench (a benchmark for refusal behavior on adversarial prompts, also from HuggingFace). All three normalize to a single internal `TestCase` format, so the scoring and storage layers have no awareness of the source.

Rubrics are YAML files that define a set of criteria, each with a passing threshold and a judge prompt. The harness ships three defaults: `refusal_detection`, `truthfulness`, and `harmlessness`. Operators can add their own without touching the Python source.

The local model backend uses the `openai` Python client pointed at an OpenAI-compatible endpoint, which means it works with both Ollama and LM Studio without any code changes. The only difference is the base URL, which is configurable via environment variable.

## The Results

The harness meets all seven success criteria defined in its brief:

- `eval run` completes end-to-end against a local Qwen 2.5 model and writes to SQLite without errors.
- `eval diff` computes and displays metric deltas between any two completed runs, including per-dataset breakdowns and flip counts.
- TruthfulQA and AdvBench load and normalize correctly from HuggingFace.
- LLM-as-judge scoring fires against each rubric criterion when `ANTHROPIC_API_KEY` is set.
- Heuristic-only mode runs fully offline, requiring no API key and no network access beyond the local model endpoint.
- The unit test suite (40 tests) passes across all scoring branches, DB roundtrip, drift computation, and dataset normalization.

The SQLite storage choice deserves a note: it was deliberate. The harness is designed for sequential, individual use, and SQLite eliminates all infrastructure overhead. The tradeoff is that concurrent writes from multiple users would collide. For the intended use case, that is an acceptable constraint, though teams running evals in parallel would need to migrate to PostgreSQL or introduce a write queue.

## What We Learned

The most useful design decision was keeping the scoring modes independent and composable rather than building a single unified scorer. Heuristic scoring is fast, free, and fully offline; LLM-as-judge is slower and costs API calls but catches subtleties that pattern matching misses. Having both available in the same run, with a clear merge rule, means the harness degrades gracefully when the API is unavailable rather than failing entirely.

The second lesson is about drift framing. A drift metric is only meaningful if it compares the same cases across runs. The decision to treat asymmetric cases (cases present in one run but not the other) as a separate count rather than forcing them into the flip calculation makes the diff output honest: it distinguishes "the model changed behavior on this case" from "this case did not exist in the previous run."

## Where to Go Next

The repository is at `projects/eval-harness/` in this workspace. The `README` covers setup, configuration, and the full command reference. The natural next step is running `eval run` against a local model, adding a small custom test suite in YAML, and then swapping model versions to see what `eval diff` surfaces.
