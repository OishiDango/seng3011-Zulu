# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface

import sys
from pathlib import Path
import subprocess


class PromedKeyManager:
    KEY_FILE = Path("promed_key.txt")

    @classmethod
    def get_key(cls):
        if not cls.KEY_FILE.exists():
            return cls.refresh_key()

        key = cls.KEY_FILE.read_text(encoding="utf-8").strip()
        if not key:
            return cls.refresh_key()

        return key

    @classmethod
    def refresh_key(cls):
        script_path = Path(__file__).resolve().parent / "get_key.py"
        subprocess.run([sys.executable, str(script_path)], check=True)

        key = cls.KEY_FILE.read_text(encoding="utf-8").strip()
        if not key:
            raise ValueError("promed_key.txt is empty after refresh.")
        return key


class PromedprojectSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # matching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class PromedprojectDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        if response.status in (401, 403):
            spider.logger.warning(f"Request got {
                response.status}. API key may have expired. Refreshing key...")

            retry_count = request.meta.get("auth_retry_count", 0)
            if retry_count >= 3:
                spider.logger.error(
                    "Maximum auth retries reached. Giving up on request."
                )
                return response

            try:
                new_key = PromedKeyManager.refresh_key()
                spider.api_key = new_key
            except Exception as e:
                spider.logger.error(f"Failed to refresh API key: {e}")
                return response

            new_url = request.url.split("?")[0] + f"?x-typesense-api-key={new_key}"
            new_request = request.replace(url=new_url, dont_filter=True)
            new_request.meta["auth_retry_count"] = retry_count + 1

            spider.logger.info(f"Retrying request with refreshed API key (attempt {
                retry_count + 1})")
            return new_request

        return response

        return response

    def process_exception(self, request, exception, spider):
        return None

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
