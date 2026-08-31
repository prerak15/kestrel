import sys
from pathlib import Path

from eval.results import Metric, ResultRecord, load

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_python_version_matches_pin():
    """The interpreter running tests must be the one we pinned."""
    pinned = (REPO_ROOT / ".python-version").read_text().strip()
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert actual == pinned, f"pinned {pinned}, running {actual}"


def test_project_layout_exists():
    """Directories the pipeline depends on must be present."""
    for name in ("eval", "tuner", "bench", "deploy", "docs/adr"):
        assert (REPO_ROOT / name).is_dir(), f"missing directory: {name}"


def test_record_captures_provenance(tmp_path):
    record = ResultRecord(
        inputs={"dataset": "smoke", "config_hash": "abc123"},
        metrics={"ndcg@10": Metric(value=0.5, ci_lower=0.4, ci_upper=0.6)},
    )
    written = load(record.write(tmp_path))

    assert written["git"]["sha"], "no git SHA captured"
    assert "dirty" in written["git"], "no dirty flag captured"
    assert written["environment"]["cores_logical"] > 0
    assert written["metrics"]["ndcg@10"]["value"] == 0.5
    assert written["schema_version"] == 1
