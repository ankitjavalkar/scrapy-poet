from collections import deque

from pytest import importorskip
from pytest_twisted import inlineCallbacks
from scrapy import Spider
from web_poet.pages import ItemWebPage

from tests.utils import EchoResource, MockServer, make_crawler

Retry = importorskip("web_poet.exceptions.Retry")


@inlineCallbacks
def test_retry_once():
    retries = deque([True, False])
    items = []

    with MockServer(EchoResource) as server:

        class ItemPage(ItemWebPage):
            def to_item(self):
                if retries.popleft():
                    raise Retry
                return {"foo": "bar"}

        class TestSpider(Spider):
            name = "test_spider"
            start_urls = [server.root_url]

            custom_settings = {
                "DOWNLOADER_MIDDLEWARES": {
                    "scrapy_poet.InjectionMiddleware": 543,
                },
                "SPIDER_MIDDLEWARES": {
                    "scrapy_poet.RetrySpiderMiddleware": 275,
                },
            }

            def parse(self, response, page: ItemPage):
                items.append(page.to_item())

        crawler = make_crawler(TestSpider, {})
        yield crawler.crawl()

    assert items == [{"foo": "bar"}]
    assert crawler.stats.get_value("downloader/request_count") == 2
    assert crawler.stats.get_value("retry/count") == 1
    assert crawler.stats.get_value("retry/reason_count/page_object_retry") == 1
    assert crawler.stats.get_value("retry/max_reached") is None


@inlineCallbacks
def test_retry_max():
    # The default value of the RETRY_TIMES Scrapy setting is 2.
    retries = deque([True, True, False])
    items = []

    with MockServer(EchoResource) as server:

        class ItemPage(ItemWebPage):
            def to_item(self):
                if retries.popleft():
                    raise Retry
                return {"foo": "bar"}

        class TestSpider(Spider):
            name = "test_spider"
            start_urls = [server.root_url]

            custom_settings = {
                "DOWNLOADER_MIDDLEWARES": {
                    "scrapy_poet.InjectionMiddleware": 543,
                },
                "SPIDER_MIDDLEWARES": {
                    "scrapy_poet.RetrySpiderMiddleware": 275,
                },
            }

            def parse(self, response, page: ItemPage):
                items.append(page.to_item())

        crawler = make_crawler(TestSpider, {})
        yield crawler.crawl()

    assert items == [{"foo": "bar"}]
    assert crawler.stats.get_value("downloader/request_count") == 3
    assert crawler.stats.get_value("retry/count") == 2
    assert crawler.stats.get_value("retry/reason_count/page_object_retry") == 2
    assert crawler.stats.get_value("retry/max_reached") is None


@inlineCallbacks
def test_retry_exceeded():
    # The default value of the RETRY_TIMES Scrapy setting is 2.
    retries = deque([True, True, True])
    items = []

    with MockServer(EchoResource) as server:

        class ItemPage(ItemWebPage):
            def to_item(self):
                if retries.popleft():
                    raise Retry
                return {"foo": "bar"}

        class TestSpider(Spider):
            name = "test_spider"
            start_urls = [server.root_url]

            custom_settings = {
                "DOWNLOADER_MIDDLEWARES": {
                    "scrapy_poet.InjectionMiddleware": 543,
                },
                "SPIDER_MIDDLEWARES": {
                    "scrapy_poet.RetrySpiderMiddleware": 275,
                },
            }

            def parse(self, response, page: ItemPage):
                items.append(page.to_item())

        crawler = make_crawler(TestSpider, {})
        yield crawler.crawl()

    assert items == []
    assert crawler.stats.get_value("downloader/request_count") == 3
    assert crawler.stats.get_value("retry/count") == 2
    assert crawler.stats.get_value("retry/reason_count/page_object_retry") == 2
    assert crawler.stats.get_value("retry/max_reached") == 1


@inlineCallbacks
def test_retry_max_configuration():
    retries = deque([True, True, True, False])
    items = []

    with MockServer(EchoResource) as server:

        class ItemPage(ItemWebPage):
            def to_item(self):
                if retries.popleft():
                    raise Retry
                return {"foo": "bar"}

        class TestSpider(Spider):
            name = "test_spider"
            start_urls = [server.root_url]

            custom_settings = {
                "DOWNLOADER_MIDDLEWARES": {
                    "scrapy_poet.InjectionMiddleware": 543,
                },
                "RETRY_TIMES": 3,
                "SPIDER_MIDDLEWARES": {
                    "scrapy_poet.RetrySpiderMiddleware": 275,
                },
            }

            def parse(self, response, page: ItemPage):
                items.append(page.to_item())

        crawler = make_crawler(TestSpider, {})
        yield crawler.crawl()

    assert items == [{"foo": "bar"}]
    assert crawler.stats.get_value("downloader/request_count") == 4
    assert crawler.stats.get_value("retry/count") == 3
    assert crawler.stats.get_value("retry/reason_count/page_object_retry") == 3
    assert crawler.stats.get_value("retry/max_reached") is None
