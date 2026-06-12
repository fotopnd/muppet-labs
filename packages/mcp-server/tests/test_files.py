import pytest
from pathlib import Path
from unittest.mock import patch

# We patch WORKSPACE_ROOT before importing tools to control the sandbox
import muppet_mcp.config as cfg


@pytest.fixture()
def workspace(tmp_path: Path):
    with patch.object(cfg, "WORKSPACE_ROOT", tmp_path):
        with patch.object(cfg, "TELEMETRY_PATH", tmp_path / ".mcp" / "telemetry.json"):
            yield tmp_path


def test_read_file_within_workspace(workspace: Path) -> None:
    from muppet_mcp.tools.files import read_monorepo_file

    (workspace / "hello.txt").write_text("world")
    result = read_monorepo_file("hello.txt")
    assert result == "world"


def test_read_file_traversal_rejected(workspace: Path) -> None:
    from muppet_mcp.tools.files import read_monorepo_file

    result = read_monorepo_file("../../etc/passwd")
    assert result.startswith("ERROR:")
    assert "traversal" in result.lower() or "outside" in result.lower()


def test_read_file_too_large(workspace: Path) -> None:
    from muppet_mcp.tools.files import read_monorepo_file

    big = workspace / "big.bin"
    big.write_bytes(b"x" * 100)
    result = read_monorepo_file("big.bin", max_bytes=50)
    assert result.startswith("ERROR:")
    assert "large" in result.lower()


def test_read_binary_file_rejected(workspace: Path) -> None:
    from muppet_mcp.tools.files import read_monorepo_file

    (workspace / "model.bin").write_bytes(bytes(range(256)))
    result = read_monorepo_file("model.bin")
    assert result.startswith("ERROR:")
    assert "binary" in result.lower()


def test_atomic_write_creates_files(workspace: Path) -> None:
    from muppet_mcp.tools.files import atomic_write_feature, FileSpec

    result = atomic_write_feature(
        [FileSpec(path="src/foo.py", content="x = 1\n")],
        manifest_note="test write",
    )
    assert result.startswith("✓")
    assert (workspace / "src" / "foo.py").read_text() == "x = 1\n"


def test_atomic_write_traversal_rejected(workspace: Path) -> None:
    from muppet_mcp.tools.files import atomic_write_feature, FileSpec

    result = atomic_write_feature(
        [FileSpec(path="../../evil.py", content="bad")],
        manifest_note="traversal attempt",
    )
    assert result.startswith("ERROR:")
    assert not (workspace / "evil.py").exists()
