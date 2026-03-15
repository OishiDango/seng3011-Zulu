from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class StatsRegionsTests(APITestCase):
    fixtures = ["alerts.json"]

    def test_stats_regions_returns_200(self):
        response = self.client.get(reverse("stats_regions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)
        self.assertIn("by_region", response.data)

    def test_stats_regions_response_structure(self):
        response = self.client.get(reverse("stats_regions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["from"], str)
        self.assertIsInstance(response.data["to"], str)
        self.assertIsInstance(response.data["by_region"], list)

    def test_stats_regions_items_have_region_and_count(self):
        response = self.client.get(reverse("stats_regions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data["by_region"]:
            self.assertIn("region", item)
            self.assertIn("count", item)
            self.assertIsInstance(item["region"], str)
            self.assertIsInstance(item["count"], int)

    def test_stats_regions_counts_are_sorted_descending(self):
        response = self.client.get(reverse("stats_regions"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        counts = [item["count"] for item in response.data["by_region"]]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_stats_regions_with_from_and_to_filters(self):
        response = self.client.get(
            reverse("stats_regions"),
            {
                "from": "2026-03-01",
                "to": "2026-03-31",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["from"], "2026-03-01")
        self.assertEqual(response.data["to"], "2026-03-31")
        self.assertIn("by_region", response.data)

    def test_stats_regions_with_disease_filter(self):
        response = self.client.get(
            reverse("stats_regions"),
            {"disease": "Measles"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("by_region", response.data)
        self.assertIsInstance(response.data["by_region"], list)

    def test_stats_regions_with_region_filter(self):
        response = self.client.get(
            reverse("stats_regions"),
            {"region": "Africa"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("by_region", response.data)
        self.assertIsInstance(response.data["by_region"], list)
