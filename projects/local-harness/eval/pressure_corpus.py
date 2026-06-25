#!/usr/bin/env python3
"""
Build the context pressure corpus: 10 base tasks × 4 context conditions + 5 two-turn chains.
Outputs pressure_tasks.json — consumed by run_pressure.py.
"""
import json
from pathlib import Path

CORPUS_PATH = Path(__file__).parent / "corpus.json"
OUT_PATH = Path(__file__).parent / "pressure_tasks.json"

SYSTEM_PROMPT = """\
You are an expert coding assistant. You have access to tools that let you read files, \
write files, run shell commands, and search the codebase. Always use the appropriate \
tool to complete the user's request. Never answer with prose when a tool call is \
required. Use tools immediately without explaining what you are about to do.

Available tools:
- read_file(path): Read file contents
- write_file(path, content): Write or overwrite a file
- run_command(cmd): Execute a shell command and return output
- search_files(pattern, directory): Search for files matching a pattern

Project structure:
  src/
    main.py         - Entry point, argument parsing, main loop
    utils.py        - Helper functions (logging, formatting, retry logic)
    api.py          - External API client with rate limiting
    models.py       - Data models and validation schemas
    config.py       - Configuration loading from env and config.json
  tests/
    test_main.py    - Integration tests for main loop
    test_utils.py   - Unit tests for helper functions
    test_api.py     - Mocked API client tests
  data/
    config.json     - Runtime configuration
    schema.json     - JSON schema for validation
  requirements.txt
  Makefile
  README.md
  pyproject.toml
  .env.example
"""

# ~1500 tokens of fake file content injected as a preceding assistant/user exchange
CONTEXT_SM = """\
Here is the current state of the relevant files for context:

--- src/main.py ---
import argparse
import logging
from src.utils import setup_logging, format_output
from src.api import APIClient
from src.config import load_config

def parse_args():
    parser = argparse.ArgumentParser(description="Data processing pipeline")
    parser.add_argument("--config", default="data/config.json")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()

def main():
    args = parse_args()
    config = load_config(args.config)
    setup_logging(verbose=args.verbose)
    client = APIClient(config["api_key"], timeout=config.get("timeout", 30))
    results = []
    for item in config["items"]:
        try:
            result = client.process(item)
            results.append(result)
        except Exception as e:
            logging.error(f"Failed to process {item}: {e}")
    print(format_output(results))

if __name__ == "__main__":
    main()

--- src/config.py ---
import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "timeout": 30,
    "retry_count": 3,
    "debug": False,
    "api_key": None,
    "items": [],
}

def load_config(path: str) -> dict:
    config = DEFAULT_CONFIG.copy()
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            file_config = json.load(f)
        config.update(file_config)
    env_key = os.environ.get("API_KEY")
    if env_key:
        config["api_key"] = env_key
    return config

--- data/config.json ---
{
  "api_key": "sk-placeholder",
  "timeout": 60,
  "debug": true,
  "items": ["item_001", "item_002", "item_003"],
  "retry_count": 5
}
"""

# ~3000 tokens: SM + additional files
CONTEXT_LG = CONTEXT_SM + """\

--- src/utils.py ---
import logging
import sys
from datetime import datetime
from typing import Any

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def format_output(results: list[Any]) -> str:
    if not results:
        return "No results."
    lines = [f"Results ({len(results)} items):"]
    for i, r in enumerate(results, 1):
        lines.append(f"  {i}. {r}")
    return "\\n".join(lines)

def retry(fn, max_attempts: int = 3, delay: float = 1.0):
    import time
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt < max_attempts - 1:
                time.sleep(delay * (attempt + 1))
    raise last_exc

--- src/api.py ---
import requests
from src.utils import retry

class APIClient:
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.example.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def process(self, item: str) -> dict:
        return retry(lambda: self._post("/process", {"item": item}))

    def _post(self, path: str, payload: dict) -> dict:
        resp = self.session.post(
            f"{self.base_url}{path}",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

--- requirements.txt ---
requests==2.31.0
python-dotenv==1.0.0
pydantic==2.5.0
pytest==7.4.3
pytest-asyncio==0.21.4
ruff==0.1.8

--- pyproject.toml ---
[project]
name = "data-pipeline"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"
"""

# Fake tool results injected after turn 1 in multi-turn chains
FAKE_TOOL_RESULTS = {
    "read_file": {
        "main.py": "# main.py\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()\n",
        "config.json": '{\n  "debug": true,\n  "timeout": 30,\n  "api_key": "sk-test"\n}\n',
        "requirements.txt": "requests==2.31.0\nflask==3.0.0\npytest==7.4.3\n",
        "README.md": "# My Project\n\nA data processing pipeline.\n\n## Installation\n\npip install -r requirements.txt\n\n## Usage\n\npython main.py\n",
    },
    "run_command": "total 12\n-rw-r--r-- 1 user staff 1234 Jan 1 00:00 main.py\n-rw-r--r-- 1 user staff  456 Jan 1 00:00 config.py\n-rw-r--r-- 1 user staff  789 Jan 1 00:00 utils.py\n",
    "search_files": '["src/main.py", "src/utils.py", "src/api.py", "tests/test_main.py"]',
    "write_file": "File written successfully.",
}

# 5 two-turn chains: (turn1_prompt, turn1_expected_tool, turn2_prompt, turn2_expected_tool)
CHAINS = [
    {
        "id": "chain_001",
        "category": "multiturn",
        "turn1": {"prompt": "Read main.py to understand the entry point.", "tool": "read_file", "params": {"path": "main.py"}},
        "turn2": {"prompt": "Now run the tests to check if it works.", "tool": "run_command", "params": {}},
        "tools": ["read_file", "run_command"],
    },
    {
        "id": "chain_002",
        "category": "multiturn",
        "turn1": {"prompt": "Search for all Python files in the src directory.", "tool": "search_files", "params": {}},
        "turn2": {"prompt": "Read the first file you found.", "tool": "read_file", "params": {}},
        "tools": ["search_files", "read_file"],
    },
    {
        "id": "chain_003",
        "category": "multiturn",
        "turn1": {"prompt": "Read requirements.txt.", "tool": "read_file", "params": {"path": "requirements.txt"}},
        "turn2": {"prompt": "Install those dependencies.", "tool": "run_command", "params": {}},
        "tools": ["read_file", "run_command"],
    },
    {
        "id": "chain_004",
        "category": "multiturn",
        "turn1": {"prompt": "Read README.md.", "tool": "read_file", "params": {"path": "README.md"}},
        "turn2": {"prompt": "Save an updated version with a Quickstart section added.", "tool": "write_file", "params": {}},
        "tools": ["read_file", "write_file"],
    },
    {
        "id": "chain_005",
        "category": "multiturn",
        "turn1": {"prompt": "List all Python files in the project.", "tool": "run_command", "params": {}},
        "turn2": {"prompt": "Read config.json.", "tool": "read_file", "params": {"path": "config.json"}},
        "tools": ["run_command", "read_file"],
    },
]

CONTEXT_LAYERS = {
    "bare": {"system": None, "context_prefix": None},
    "sysprompt": {"system": SYSTEM_PROMPT, "context_prefix": None},
    "context_sm": {"system": SYSTEM_PROMPT, "context_prefix": CONTEXT_SM},
    "context_lg": {"system": SYSTEM_PROMPT, "context_prefix": CONTEXT_LG},
}


def build() -> list[dict]:
    corpus = json.loads(CORPUS_PATH.read_text())
    # Pick 10 tasks: balanced across categories
    selected_ids = [
        "single_read_001", "single_read_004",
        "single_write_001", "single_write_004",
        "single_cmd_001", "single_cmd_004",
        "single_search_001", "single_search_002",
        "seq_001", "cond_001",
    ]
    base_tasks = [t for t in corpus if t["id"] in selected_ids]

    tasks = []

    # Single-turn tasks × 4 context conditions
    for task in base_tasks:
        for condition, layer in CONTEXT_LAYERS.items():
            tasks.append({
                "id": f"{task['id']}__{condition}",
                "base_id": task["id"],
                "category": task["category"],
                "condition": condition,
                "tools": task["tools"],
                "expected_tool": task["expected_tool"],
                "check_params": task["check_params"],
                "expected_params": task["expected_params"],
                "system": layer["system"],
                "context_prefix": layer["context_prefix"],
                "prompt": task["prompt"],
                "multiturn": False,
            })

    # Multi-turn chains (sysprompt + context_sm only — realistic condition)
    for chain in CHAINS:
        tasks.append({
            "id": chain["id"],
            "base_id": chain["id"],
            "category": "multiturn",
            "condition": "context_sm",
            "tools": chain["tools"],
            "expected_tool": chain["turn1"]["tool"],
            "check_params": False,
            "expected_params": {},
            "system": SYSTEM_PROMPT,
            "context_prefix": CONTEXT_SM,
            "prompt": chain["turn1"]["prompt"],
            "multiturn": True,
            "turn2_prompt": chain["turn2"]["prompt"],
            "turn2_expected_tool": chain["turn2"]["tool"],
            "fake_tool_result": FAKE_TOOL_RESULTS.get(chain["turn1"]["tool"], "Done."),
        })

    return tasks


def main():
    tasks = build()
    OUT_PATH.write_text(json.dumps(tasks, indent=2))
    by_condition = {}
    for t in tasks:
        c = t["condition"]
        by_condition[c] = by_condition.get(c, 0) + 1
    print(f"Built {len(tasks)} pressure tasks → {OUT_PATH}")
    for c, n in sorted(by_condition.items()):
        print(f"  {c:<15} {n}")


if __name__ == "__main__":
    main()
