"""Run the real-site test spider with each browser provider and measure the whole crawl.

CPU seconds (user + system, summed over every process in the crawl) stands in for energy.
Usage: python benchmarks/scrapy_bench.py [runs]
"""

import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

import psutil

SPIDER = Path(__file__).parent.parent / "tests" / "quotes_spider.py"
SETUPS = {
    "Lightpanda": ["-s", "PLAYWRIGHT_BROWSER_PROVIDER=scrapy_lightpanda.LightpandaBrowserProvider"],
    "Chromium headless": ["-s", "PLAYWRIGHT_BROWSER_PROVIDER=scrapy_playwright.provider.PlaywrightBrowserProvider"],
    # Same one-page-at-a-time limit Lightpanda has, for a like-for-like comparison.
    "Chromium headless, 1 page": ["-s", "PLAYWRIGHT_BROWSER_PROVIDER=scrapy_playwright.provider.PlaywrightBrowserProvider",
                                  "-s", "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT=1"],
}


def crawl(extra):
    out = Path(tempfile.mkdtemp()) / "out.jsonl"
    t0 = time.time()
    proc = psutil.Popen([sys.executable, "-m", "scrapy", "runspider", str(SPIDER), "-o", f"{out}:jsonlines",
                         "-L", "ERROR", *extra])
    cpu, peak = {}, 0
    while proc.poll() is None:
        rss = 0
        for p in [proc, *proc.children(recursive=True)]:
            try:
                t = p.cpu_times()
                cpu[p.pid] = t.user + t.system  # last sample per pid; children_* skipped to avoid double counting
                rss += p.memory_info().rss
            except psutil.Error:
                pass
        peak = max(peak, rss)
        time.sleep(0.05)
    wall = time.time() - t0
    rows = [json.loads(line) for line in out.read_text().splitlines()] if out.exists() else []
    good = sum(1 for r in rows if r["text"] and r["author"])
    return {"cpu": sum(cpu.values()), "mb": peak / 2**20, "wall": wall, "items": good}


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print("| Browser | Items | CPU time (s) | Peak RAM (MB) | Wall time (s) |")
    print("|---|---|---|---|---|")
    for name, extra in SETUPS.items():
        res = [crawl(extra) for _ in range(runs)]
        med = {k: statistics.median(r[k] for r in res) for k in ("cpu", "mb", "wall")}
        items = "/".join(str(r["items"]) for r in res)
        print(f"| {name} | {items} | {med['cpu']:.2f} | {med['mb']:.0f} | {med['wall']:.1f} |", flush=True)
