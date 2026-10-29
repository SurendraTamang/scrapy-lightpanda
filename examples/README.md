# Examples

Each spider is self-contained: copy its `custom_settings` into your project's `settings.py`, or run it as is.
They target [toscrape.com](https://toscrape.com), a sandbox made for scraping practice.

| Example | Shows | Run |
|---|---|---|
| [js_pagination.py](js_pagination.py) | Follow "Next" links on a JavaScript-rendered site | `scrapy runspider examples/js_pagination.py -o quotes.jsonl` |
| [infinite_scroll.py](infinite_scroll.py) | Scroll with `playwright_include_page` until no new items load | `scrapy runspider examples/infinite_scroll.py -o quotes.jsonl` |
| [delayed_content.py](delayed_content.py) | Wait for late JavaScript content with `PageMethod("wait_for_selector", ...)` | `scrapy runspider examples/delayed_content.py -o quotes.jsonl` |

All three are run in CI by `tests/test_examples.py`.
