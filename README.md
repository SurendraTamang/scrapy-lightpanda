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
