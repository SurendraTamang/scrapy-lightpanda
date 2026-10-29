"""Scroll an infinite-scroll page until no new items load, then parse the final page.

Run: scrapy runspider examples/infinite_scroll.py -o quotes.jsonl
"""

import scrapy


class InfiniteScrollSpider(scrapy.Spider):
    name = "infinite_scroll"
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
            "https://quotes.toscrape.com/scroll",
            meta={"playwright": True, "playwright_include_page": True},
            errback=self.close_page,
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        try:
            await page.wait_for_selector("div.quote")
            count = 0
            while count != (count := await page.locator("div.quote").count()):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)  # let the next /api/quotes batch render
            html = await page.content()
        finally:
            await page.close()

        for quote in scrapy.Selector(text=html).css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
            }

    async def close_page(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
