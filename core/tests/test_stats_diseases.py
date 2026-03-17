from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestsStatsDiseases(APITestCase):
    fixtures = ["alerts.json"]

    def setUp(self):
        self.url = reverse("stats_diseases")

    def test_stats_diseases_returns_200(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stats_diseases_returns_expected_keys(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)
        self.assertIn("by_disease", response.data)

    def test_stats_diseases_returns_list(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["by_disease"], list)

    def test_stats_diseases_returns_expected_counts_for_sample_range(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["from"], "2026-02-10")
        self.assertEqual(response.data["to"], "2026-03-12")

        disease_counts = {
            item["disease"]: item["count"]
            for item in response.data["by_disease"]
        }

        self.assertEqual(
            disease_counts,
            {
                "Measles": 3,
                "Avian Influenza": 1,
                "Hepatitis E": 1,
                "Leptospirosis": 1,
                "Myiasis": 1,
            },
        )

    def test_stats_diseases_filters_by_id(self):
        response = self.client.get(self.url, {"id": "8731241"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        disease_counts = {
            item["disease"]: item["count"]
            for item in response.data["by_disease"]
        }

        self.assertEqual(
            disease_counts,
            {
                "Hepatitis E": 1,
                "Leptospirosis": 1,
            },
        )

    def test_stats_diseases_filters_by_region(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "region": "North America",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        disease_counts = {
            item["disease"]: item["count"]
            for item in response.data["by_disease"]
        }

        self.assertEqual(
            disease_counts,
            {
                "Measles": 3,
                "Myiasis": 1,
                "Salmonella": 1,
                "Legionnaires": 1,
            },
        )

    def test_stats_diseases_filters_by_species_humans(self):
        response = self.client.get(
            self.url,
            {
                "from": "2026-02-01",
                "to": "2026-03-31",
                "species": "Humans",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        disease_counts = {
            item["disease"]: item["count"]
            for item in response.data["by_disease"]
        }

        self.assertEqual(
            disease_counts,
            {
                "Measles": 3,
                "Food-related toxin": 1,
                "Hepatitis E": 1,
                "Legionnaires": 1,
                "Leptospirosis": 1,
                "Myiasis": 1,
                "Salmonella": 2,
                "Shigellosis": 1,
            },
        )
        self.assertNotIn("Avian Influenza", disease_counts)

    def test_stats_diseases_filters_by_location_mexico(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "location": "Mexico",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        disease_counts = {
            item["disease"]: item["count"]
            for item in response.data["by_disease"]
        }

        # includes New Mexico because location uses icontains
        self.assertEqual(
            disease_counts,
            {
                "Measles": 3,
                "Myiasis": 1,
            },
        )

    def test_stats_diseases_returns_empty_list_when_no_match(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "disease": "Smallpox",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["by_disease"], [])

    def test_stats_diseases_is_sorted_by_count_desc_then_name(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-10", "to": "2026-03-12"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        by_disease = response.data["by_disease"]

        self.assertEqual(by_disease[0], {"disease": "Measles", "count": 3})

        remaining_names = [item["disease"] for item in by_disease[1:]]
        self.assertEqual(
            remaining_names,
            [
                "Avian Influenza",
                "Hepatitis E",
                "Leptospirosis",
                "Myiasis",
            ],
        )

    def test_stats_diseases_default_window_returns_from_to(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)

    def test_stats_diseases_multiple_disease_filter_only_counts_requested_disease(self):
        response = self.client.get(
            self.url,
            {
                "from": "2023-01-01",
                "to": "2026-12-31",
                "disease": ["Measles", "Salmonella"],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        disease_counts = {
            item["disease"]: item["count"]
            for item in response.data["by_disease"]
        }

        self.assertEqual(
            disease_counts,
            {
                "Measles": 9,
                "Salmonella": 4,
            },
        )
        self.assertNotIn("Shigellosis", disease_counts)
