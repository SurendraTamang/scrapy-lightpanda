import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest
from scrapy.exceptions import NotConfigured

from scrapy_lightpanda import LightpandaBrowserProvider

HERE = Path(__file__).parent


def test_rejects_unsupported_launch_option():
    config = SimpleNamespace(launch_options={"headless": True}, cdp_kwargs={}, max_pages_per_context=16)
    with pytest.raises(NotConfigured, match="headless"):
        LightpandaBrowserProvider(config)


def test_missing_binary(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(NotConfigured, match="not found"):
        LightpandaBrowserProvider(SimpleNamespace(launch_options={}, cdp_kwargs={}))


@pytest.mark.network
def test_crawls_js_site(tmp_path):
    out = tmp_path / "quotes.jsonl"
    before = {p.pid for p in psutil.process_iter(["name"]) if p.info["name"] == "lightpanda"}
    proc = subprocess.run(
        [sys.executable, "-m", "scrapy", "runspider", str(HERE / "quotes_spider.py"),
         "-o", f"{out}:jsonlines", "-L", "INFO"],
        capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "'downloader/response_status_count/200': 10" in proc.stderr

    rows = [json.loads(line) for line in out.read_text().splitlines()]
    # Content checks, not just counts: every quote rendered by JS, no blanks or duplicates.
    assert len(rows) == 100
    assert all(r["text"] and r["text"].startswith("“") and r["author"] for r in rows)
    assert len({r["text"] for r in rows}) == 100
    assert len({r["author"] for r in rows}) == 50
    assert any(r["author"] == "Albert Einstein" for r in rows)

    after = {p.pid for p in psutil.process_iter(["name"]) if p.info["name"] == "lightpanda"}
    assert after <= before, "lightpanda process left running after crawl"
