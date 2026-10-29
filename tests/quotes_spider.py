"""Real-site spider: quotes.toscrape.com/js only shows quotes when JavaScript runs."""

import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_PROVIDER": "scrapy_lightpanda.LightpandaBrowserProvider",
    }

    async def start(self):
        # All 10 pages at once, to exercise concurrent pages on one Lightpanda process.
        for n in range(1, 11):
            yield scrapy.Request(f"https://quotes.toscrape.com/js/page/{n}/", meta={"playwright": True})

    def parse(self, response):
        for q in response.css("div.quote"):
            yield {
                "text": q.css("span.text::text").get(),
                "author": q.css("small.author::text").get(),
                "tags": q.css("a.tag::text").getall(),
            }
