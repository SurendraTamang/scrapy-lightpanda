# scrapy-lightpanda

[![test](https://github.com/SurendraTamang/scrapy-lightpanda/actions/workflows/test.yml/badge.svg)](https://github.com/SurendraTamang/scrapy-lightpanda/actions/workflows/test.yml)

Scrape JavaScript-rendered sites with [Scrapy](https://scrapy.org) + [scrapy-playwright](https://github.com/scrapy-plugins/scrapy-playwright) on [Lightpanda](https://github.com/lightpanda-io/browser), a headless browser built for web scraping and automation. In our benchmark it used about half the CPU and a third of the memory of headless Chromium.

It is a single `PLAYWRIGHT_BROWSER_PROVIDER` for scrapy-playwright. It starts `lightpanda serve` on a free local port when the first browser page is needed, connects over CDP, and stops the process when the crawl ends. Your spiders do not change.

## Install

```bash
pip install scrapy-lightpanda
```

Install the Lightpanda binary and put it on your `PATH` (see [Lightpanda install docs](https://github.com/lightpanda-io/browser#install)):

```bash
# macOS (Apple Silicon)
curl -L -o lightpanda https://github.com/lightpanda-io/browser/releases/latest/download/lightpanda-aarch64-macos
chmod +x lightpanda && mv lightpanda ~/.local/bin/
```

## Usage

```python
# settings.py
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_PROVIDER = "scrapy_lightpanda.LightpandaBrowserProvider"
```

Then request pages with `meta={"playwright": True}`, as with any scrapy-playwright spider.

### Options

`PLAYWRIGHT_LAUNCH_OPTIONS` is reused for the Lightpanda process:

| Key | Default | Meaning |
|---|---|---|
| `executable_path` | `lightpanda` on `PATH` | Path to the binary |
| `args` | `[]` | Extra `lightpanda serve` flags, e.g. `["--disable-features", "cors"]` |
| `env` | `{}` | Extra environment variables |
| `timeout` | `10000` | Milliseconds to wait for Lightpanda to start |

Any other key raises `NotConfigured`, because Lightpanda is not launched through Playwright.

Telemetry: Lightpanda sends usage telemetry by default. This provider sets `LIGHTPANDA_DISABLE_TELEMETRY=true` unless you set it yourself.

## Benchmark

Measured on an Apple Silicon Mac (macOS 26, Python 3.14, Lightpanda 1.0.2, Chromium Headless Shell 151, Camoufox 156.0.1-beta.36), October 2026. CPU time is user + system time summed over every process involved, and stands in for energy use. Your numbers will differ; rerun the scripts in `benchmarks/`.

### Full Scrapy crawl

The test spider crawls all 10 pages of [quotes.toscrape.com/js](https://quotes.toscrape.com/js/) (JavaScript-rendered). Median of 3 runs. Numbers cover the whole crawl: Scrapy, the Playwright driver and the browser.

| Browser | Complete items per run | CPU time (s) | Peak RAM (MB) | Wall time (s) |
|---|---|---|---|---|
| **Lightpanda** | 100/100/100 | **2.03** | **434** | 8.2 |
| Chromium headless | 100/100/100 | 3.69 | 1340 | **4.7** |
| Chromium headless, 1 page at a time | 100/100/100 | 3.86 | 695 | 13.3 |

`python benchmarks/scrapy_bench.py 3`

Lightpanda used about half the CPU and a third of the memory of Chromium. Chromium finished faster because it loads pages in parallel; with the same one-page limit, it was slower than Lightpanda.

### Browser only

Each browser launched and loaded the page 5 times, driven by Playwright. Single run.

| Site | Lightpanda | Chromium headless | Camoufox |
|---|---|---|---|
| Hacker News | **0.27 s CPU · 55 MB** | 0.76 s · 338 MB | 35.3 s · 2672 MB (4/5 loads) |
| Wikipedia article | **0.81 s · 90 MB** | 1.70 s · 496 MB | 39.6 s · 2370 MB |
| BBC News | **4.41 s · 144 MB** | 6.88 s · 758 MB | 42.4 s · 2510 MB |

`python benchmarks/browsers_bench.py` (needs `camoufox`)

Camoufox is an anti-detection Firefox and pays a large fixed startup cost. Use it only for sites that block other browsers.

## Limitations

- One page at a time. A Lightpanda CDP connection holds a single browser context with a single page, so the provider sets `PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 1` and browser requests queue instead of failing. Named contexts (`playwright_context` meta) other than the default are not supported. Plain (non-`playwright`) requests still run concurrently.
- Lightpanda does not implement every Web API yet. Complex single-page apps may fail; fall back to the default provider for those.
- No screenshots (Lightpanda does not render pixels).
- No persistent contexts (`user_data_dir`).
- Lightpanda's text extraction can include text that a real browser would hide with CSS.

## Tests

The tests crawl a real JavaScript-rendered site (quotes.toscrape.com/js) and check the scraped content, not just the item count.

```bash
pip install -e '.[test]'
pytest            # needs network and the lightpanda binary
pytest -m "not network"
```

## License

BSD-3-Clause, same as Scrapy and scrapy-playwright. Not affiliated with Lightpanda or the Scrapy project.
