"""Wait for content that JavaScript adds after a delay (here, 10 seconds).

Run: scrapy runspider examples/delayed_content.py -o quotes.jsonl
"""

import scrapy
from scrapy_playwright.page import PageMethod


class DelayedContentSpider(scrapy.Spider):
    name = "delayed_content"
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_PROVIDER": "scrapy_lightpanda.LightpandaBrowserProvider",
    }

    async def start(self):
        yield scrapy.Request(
            "https://quotes.toscrape.com/js-delayed/",
            meta={
                "playwright": True,
                "playwright_page_methods": [PageMethod("wait_for_selector", "div.quote", timeout=20_000)],
            },
        )

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
            }
