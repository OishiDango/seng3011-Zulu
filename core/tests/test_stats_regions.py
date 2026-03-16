from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestsStatsRegions(APITestCase):
    fixtures = ["alerts.json"]

    def setUp(self):
        self.url = reverse("stats_regions")

    def test_stats_regions_returns_200(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stats_regions_returns_expected_keys(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)
        self.assertIn("by_region", response.data)

    def test_stats_regions_returns_list(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["by_region"], list)

    def test_stats_regions_returns_expected_counts_for_sample_range(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["from"], "2026-02-10")
        self.assertEqual(response.data["to"], "2026-03-12")

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        self.assertEqual(
            region_counts,
            {
                "North America": 4,
                "South America": 2,
                "Asia": 1,
            },
        )

    def test_stats_regions_filters_by_id(self):
        response = self.client.get(self.url, {"id": "8731230"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        self.assertEqual(
            region_counts,
            {
                "North America": 1,
                "South America": 1,
            },
        )

    def test_stats_regions_filters_by_disease_measles(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "disease": "Measles",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        self.assertEqual(
            region_counts,
            {
                "North America": 6,
                "Asia": 2,
                "Europe": 1,
                "South America": 1,
            },
        )

    def test_stats_regions_filters_by_species_humans(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "species": "Humans",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        self.assertEqual(
            region_counts,
            {
                "North America": 6,
                "Europe": 2,
                "Asia": 1,
                "Africa": 1,
                "South America": 1,
            },
        )

    def test_stats_regions_filters_by_location_mexico(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "location": "Mexico",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        # includes New Mexico because location filtering uses icontains
        self.assertEqual(
            region_counts,
            {
                "North America": 4,
                "South America": 1,
            },
        )

    def test_stats_regions_returns_empty_list_when_no_match(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "disease": "Smallpox",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["by_region"], [])

    def test_stats_regions_is_sorted_by_count_desc_then_name(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        by_region = response.data["by_region"]

        self.assertEqual(by_region[0], {"region": "North America", "count": 4})

        remaining_names = [item["region"] for item in by_region[1:]]
        self.assertEqual(remaining_names, ["South America", "Asia"])

    def test_stats_regions_default_window_returns_from_to(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)

    def test_stats_regions_multiple_region_filter_only_counts_requested_regions(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "region": ["North America", "Europe"],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        self.assertEqual(
            region_counts,
            {
                "North America": 17,
                "Europe": 8,
            },
        )
        self.assertNotIn("Asia", region_counts)
        self.assertNotIn("Africa", region_counts)
        self.assertNotIn("South America", region_counts)

    def test_stats_regions_filters_by_single_region_only_counts_that_region(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "region": "Europe",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        region_counts = {
            item["region"]: item["count"]
            for item in response.data["by_region"]
        }

        self.assertEqual(region_counts, {"Europe": 8})
