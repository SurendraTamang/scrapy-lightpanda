"""Follow "Next" links across a JavaScript-rendered site.

Run: scrapy runspider examples/js_pagination.py -o quotes.jsonl
"""

import scrapy


class JsPaginationSpider(scrapy.Spider):
    name = "js_pagination"
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_PROVIDER": "scrapy_lightpanda.LightpandaBrowserProvider",
    }

    async def start(self):
        yield scrapy.Request("https://quotes.toscrape.com/js/", meta={"playwright": True})

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("a.tag::text").getall(),
            }
        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, meta={"playwright": True})
