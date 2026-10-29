import json
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).parent.parent / "examples"


@pytest.mark.network
@pytest.mark.parametrize("name, items, authors", [
    ("js_pagination", 100, 50),
    ("infinite_scroll", 100, 50),
    ("delayed_content", 10, 8),
])
def test_example(tmp_path, name, items, authors):
    out = tmp_path / "out.jsonl"
    proc = subprocess.run(
        [sys.executable, "-m", "scrapy", "runspider", str(EXAMPLES / f"{name}.py"), "-o", f"{out}:jsonlines"],
        capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == items
    assert all(r["text"] and r["author"] for r in rows)
    assert len({r["text"] for r in rows}) == items
    assert len({r["author"] for r in rows}) == authors
