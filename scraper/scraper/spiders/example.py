import json
from datetime import UTC, datetime
from pathlib import Path

import scrapy


class PromedSpider(scrapy.Spider):
    name = "example"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "LOG_LEVEL": "INFO",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        key_path = Path("promed_key.txt")
        if not key_path.exists():
            raise FileNotFoundError("promed_key.txt not found. Run get_key.py first.")

        self.api_key = key_path.read_text(encoding="utf-8").strip()
        if not self.api_key:
            raise ValueError("promed_key.txt is empty.")

        self.item_count = 0

    def start_requests(self):
        yield self.make_request(page=1)

    def make_request(self, page):
        api_url = (
            "https://vcil9zn2w7dhj8kpp.a1.typesense.net/multi_search"
            f"?x-typesense-api-key={self.api_key}"
        )

        search_fields = (
            "full_text,post_title,subject_line,"
            "moderator_comments,places,diseases,species"
        )

        payload = {
            "searches": [
                {
                    "collection": "alerts",
                    "facet_by": "issue_date,network",
                    "filter_by": "network:=[`ProMED Mail`]",
                    "highlight_full_fields": search_fields,
                    "max_facet_values": 50,
                    "min_len_1typo": 6,
                    "min_len_2typo": 9,
                    "page": page,
                    "q": "*",
                    "query_by": search_fields,
                },
                {
                    "collection": "alerts",
                    "facet_by": "network",
                    "highlight_full_fields": search_fields,
                    "max_facet_values": 50,
                    "min_len_1typo": 6,
                    "min_len_2typo": 9,
                    "page": 1,
                    "per_page": 0,
                    "q": "*",
                    "query_by": search_fields,
                },
            ]
        }

        return scrapy.Request(
            url=api_url,
            method="POST",
            body=json.dumps(payload),
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "text/plain",
                "Origin": "https://www.promedmail.org",
                "Referer": "https://www.promedmail.org/",
            },
            callback=self.parse,
            cb_kwargs={"page": page},
            dont_filter=True,
        )

    def extract_names(self, items):
        if not items:
            return []
        return [item.get("name") for item in items if item.get("name")]

    def extract_regions(self, places):
        if not places:
            return []

        regions = []
        seen = set()

        for place in places:
            location = place.get("location", {})
            continent = location.get("continent")
            if continent and continent not in seen:
                seen.add(continent)
                regions.append(continent)

        return regions

    def extract_locations(self, places):
        if not places:
            return []

        cleaned_locations = []

        for place in places:
            location = place.get("location", {})
            country = location.get("country") or place.get("country")
            region = location.get("region")
            locality = location.get("locality")

            cleaned_locations.append(
                [
                    country or "",
                    region or "",
                    locality or "",
                ]
            )

        return cleaned_locations

    def format_date(self, timestamp):
        if not timestamp:
            return None
        return datetime.fromtimestamp(timestamp, UTC).date().isoformat()

    def parse(self, response, page):
        if response.status != 200:
            self.logger.error(f"Page {page} failed with status {response.status}")
            self.logger.error(response.text)
            return

        data = json.loads(response.text)
        hits = data["results"][0].get("hits", [])

        self.logger.info(f"Page {page}: scraped {len(hits)} alerts")

        for hit in hits:
            doc = hit["document"]
            self.item_count += 1

            external_id = str(doc.get("alert_id"))
            title = doc.get("post_title")
            diseases = self.extract_names(doc.get("diseases"))
            species = self.extract_names(doc.get("species"))
            places = doc.get("places")
            regions = self.extract_regions(places)
            locations = self.extract_locations(places)
            date = self.format_date(doc.get("issue_date"))

            self.logger.info(
                f"data #{self.item_count} | page={page} | alert_id={external_id}"
            )

            yield {
                "model": "core.alert",
                "pk": self.item_count,
                "fields": {
                    "external_id": external_id,
                    "date": date,
                    "title": title,
                    "diseases": diseases,
                    "species": species,
                    "regions": regions,
                    "locations": locations,
                },
            }

        if hits:
            yield self.make_request(page + 1)
