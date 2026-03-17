from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestsStatsTimeseries(APITestCase):
    fixtures = ["alerts.json"]

    def setUp(self):
        self.url = reverse("stats_timeseries")

    def test_stats_timeseries_returns_200(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-01", "to": "2026-03-31"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stats_timeseries_returns_expected_keys(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-01", "to": "2026-03-31"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("interval", response.data)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)
        self.assertIn("results", response.data)

    def test_stats_timeseries_default_interval_is_day(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-01", "to": "2026-03-31"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["interval"], "day")

    def test_stats_timeseries_invalid_interval_returns_400(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "year",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid interval")

    def test_stats_timeseries_day_interval_counts(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "day",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["interval"], "day")
        self.assertEqual(response.data["from"], "2026-02-01")
        self.assertEqual(response.data["to"], "2026-03-31")

        results = response.data["results"]
        period_counts = {item["period"]: item["count"] for item in results}

        self.assertEqual(
            period_counts,
            {
                "2026-02-02": 1,
                "2026-02-06": 2,
                "2026-02-07": 1,
                "2026-02-16": 1,
                "2026-03-03": 1,
                "2026-03-04": 1,
                "2026-03-05": 3,
            },
        )

    def test_stats_timeseries_week_interval_counts(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "week",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["interval"], "week")

        results = response.data["results"]
        period_counts = {item["period"]: item["count"] for item in results}

        self.assertEqual(
            period_counts,
            {
                "2026-02-02": 4,
                "2026-02-16": 1,
                "2026-03-02": 5,
            },
        )

    def test_stats_timeseries_month_interval_counts(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "month",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["interval"], "month")

        results = response.data["results"]
        period_counts = {item["period"]: item["count"] for item in results}

        self.assertEqual(
            period_counts,
            {
                "2026-02-01": 5,
                "2026-03-01": 5,
            },
        )

    def test_stats_timeseries_results_are_ordered(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "day",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        periods = [item["period"] for item in response.data["results"]]
        self.assertEqual(periods, sorted(periods))

    def test_stats_timeseries_filters_by_disease(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "day",
                "disease": "Measles",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        period_counts = {
            item["period"]: item["count"]
            for item in response.data["results"]
        }

        self.assertEqual(
            period_counts,
            {
                "2026-02-16": 1,
                "2026-03-03": 1,
                "2026-03-05": 1,
            },
        )

    def test_stats_timeseries_filters_by_region(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "interval": "day",
                "region": "North America",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        period_counts = {
            item["period"]: item["count"]
            for item in response.data["results"]
        }

        self.assertEqual(
            period_counts,
            {
                "2026-02-02": 1,
                "2026-02-07": 1,
                "2026-02-16": 1,
                "2026-03-03": 1,
                "2026-03-05": 2,
            },
        )

    def test_stats_timeseries_returns_empty_results_when_no_match(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "disease": "Smallpox",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])
