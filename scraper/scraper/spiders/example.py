import scrapy
import json
from pathlib import Path
from datetime import datetime, timezone

def clean_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    if value == "" or value.lower() in {"null", "none", "string"}:
        return None

    return value


def unique_list_keep_order(values):
    seen = set()
    result = []

    for value in values:
        if value is None:
            continue

        key = tuple(value) if isinstance(value, list) else value
        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


def unix_to_date_string(timestamp):
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")


def extract_diseases(alert):
    diseases = []
    for item in alert.get("diseases", []):
        name = clean_text(item.get("name"))
        if name:
            diseases.append(name)
    return unique_list_keep_order(diseases)


def extract_species(alert):
    species = []
    for item in alert.get("species", []):
        name = clean_text(item.get("name"))
        if name:
            species.append(name)
    return unique_list_keep_order(species)


def extract_regions(alert):
    regions = []
    for loc in alert.get("locations", []):
        location_info = loc.get("location", {})
        continent = clean_text(location_info.get("continent"))
        if continent:
            regions.append(continent)
    return unique_list_keep_order(regions)


def extract_locations(alert):
    locations = []

    for loc in alert.get("locations", []):
        location_info = loc.get("location", {})

        country = clean_text(location_info.get("country") or loc.get("country"))
        region = clean_text(location_info.get("region"))
        locality = clean_text(location_info.get("locality"))

        parts = []

        if country:
            parts.append(country)

        if region:
            parts.append(region)

        if locality:
            parts.append(locality)

        if parts:  
            locations.append(parts)

    return unique_list_keep_order(locations)

def transform_alert(alert, pk):
    return {
        "model": "core.alert",
        "pk": pk,
        "fields": {
            "external_id": str(alert.get("alert_id")),
            "date": unix_to_date_string(alert.get("issue_date")),
            "title": alert.get("title"),
            "diseases": extract_diseases(alert),
            "species": extract_species(alert),
            "regions": extract_regions(alert),
            "locations": extract_locations(alert)
        }
    }


class PromedSpider(scrapy.Spider):
    name = "example"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        key_path = Path("promed_key.txt")
        if not key_path.exists():
            raise FileNotFoundError(
                "promed_key.txt not found. Run get_key.py first."
            )

        self.api_key = key_path.read_text(encoding="utf-8").strip()
        if not self.api_key:
            raise ValueError("promed_key.txt is empty.")

        self.pk_counter = 1

    def start_requests(self):
        yield self.make_request(page=1)

    def make_request(self, page):
        api_url = (
            "https://vcil9zn2w7dhj8kpp.a1.typesense.net/multi_search"
            f"?x-typesense-api-key={self.api_key}"
        )

        payload = {
            "searches": [
                {
                    "collection": "alerts",
                    "facet_by": "issue_date,network",
                    "filter_by": "network:=[`ProMED Mail`]",
                    "highlight_full_fields": "full_text,post_title,subject_line,moderator_comments,places,diseases,species",
                    "max_facet_values": 50,
                    "min_len_1typo": 6,
                    "min_len_2typo": 9,
                    "page": page,
                    "q": "*",
                    "query_by": "full_text,post_title,subject_line,moderator_comments,places,diseases,species",
                },
                {
                    "collection": "alerts",
                    "facet_by": "network",
                    "highlight_full_fields": "full_text,post_title,subject_line,moderator_comments,places,diseases,species",
                    "max_facet_values": 50,
                    "min_len_1typo": 6,
                    "min_len_2typo": 9,
                    "page": 1,
                    "per_page": 0,
                    "q": "*",
                    "query_by": "full_text,post_title,subject_line,moderator_comments,places,diseases,species",
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

            raw_alert = {
                "page": page,
                "alert_id": doc.get("alert_id"),
                "title": doc.get("post_title"),
                "diseases": doc.get("diseases"),
                "species": doc.get("species"),
                "locations": doc.get("places"),
                "issue_date": doc.get("issue_date"),
                "network": doc.get("network"),
            }

            transformed = transform_alert(raw_alert, self.pk_counter)
            self.pk_counter += 1

            yield transformed

        if hits:
            yield self.make_request(page + 1)