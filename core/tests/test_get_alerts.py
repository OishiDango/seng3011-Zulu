from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestsGetAlerts(APITestCase):
    fixtures = ["alerts.json"]

    def setUp(self):
        self.url = reverse("alerts")

    def test_get_alerts_returns_200(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("alerts", response.data)
        self.assertIn("from", response.data)
        self.assertIn("to", response.data)

    def test_get_alerts_returns_alert_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data["alerts"], list)

    def test_get_alerts_filters_by_id(self):
        response = self.client.get(self.url, {"id": "8731272"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["alerts"]), 1)
        self.assertEqual(response.data["alerts"][0]["id"], "8731272")

    def test_get_alerts_filters_by_disease_measles(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "disease": "Measles"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {
                "8731272",
                "8731230",
                "8730433",
                "8730891",
                "8726506",
                "8726280",
                "8720061",
                "8719909",
                "8728922",
            },
        )

    def test_get_alerts_filters_by_disease_salmonella(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "disease": "Salmonella"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {"8730623", "8730649", "8730105", "8723314"},
        )

    def test_get_alerts_filters_by_species_humans(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "species": "Humans"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(len(returned_ids), 33)
        self.assertIn("8731272", returned_ids)
        self.assertIn("8712386", returned_ids)
        self.assertNotIn("8720357", returned_ids)
        self.assertNotIn("8720318", returned_ids)
        self.assertNotIn("8713622", returned_ids)

    def test_get_alerts_filters_by_species_cows(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "species": "Cows"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(returned_ids, {"8720318", "8720063", "8712134"})

    def test_get_alerts_filters_by_region_north_america(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "region": "North America"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {
                "8731272",
                "8731256",
                "8731230",
                "8730433",
                "8730891",
                "8726506",
                "8726280",
                "8730649",
                "8730512",
                "8730105",
                "8729376",
                "8720687",
                "8716456",
                "8714314",
                "8719727",
                "8713120",
                "8712134",
            },
        )

    def test_get_alerts_filters_by_region_europe(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "region": "Europe"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {
                "8730623",
                "8730620",
                "8730293",
                "8728907",
                "8727600",
                "8723314",
                "8721537",
                "8728922",
            },
        )

    def test_get_alerts_filters_by_location_mexico(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "location": "Mexico"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(returned_ids, {"8731272", "8731256", "8731230", "8730433"})

    def test_get_alerts_filters_by_location_united_states(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "location": "United States"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertIn("8731272", returned_ids)
        self.assertIn("8730649", returned_ids)
        self.assertIn("8712134", returned_ids)
        self.assertNotIn("8731269", returned_ids)

    def test_get_alerts_filters_by_from_date(self):
        response = self.client.get(self.url, {"from": "2026-02-01", "to": "2026-12-31"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {
                "8731272",
                "8731269",
                "8731256",
                "8731241",
                "8731230",
                "8730623",
                "8730620",
                "8730891",
                "8730649",
                "8730512",
            },
        )

    def test_get_alerts_filters_by_to_date(self):
        response = self.client.get(self.url, {"to": "2025-01-31"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["from"], "2024-02-01")
        self.assertEqual(response.data["to"], "2025-01-31")

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {"8721537", "8720687", "8720621",
             "8720357", "8720318", "8720063",
             "8720061", "8719909", "8719386",
             "8719727", "8716456"},
        )

    def test_get_alerts_filters_by_date_range(self):
        response = self.client.get(
            self.url,
            {"from": "2026-02-01", "to": "2026-02-28"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}
        self.assertEqual(
            returned_ids,
            {
                "8730623",
                "8730620",
                "8730891",
                "8730649",
                "8730512",
            },
        )

    def test_get_alerts_filters_by_multiple_regions_or_logic(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "region": ["Asia", "Africa"]},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {alert["id"] for alert in response.data["alerts"]}

        self.assertEqual(
            returned_ids,
            {
                "8731241",
                "8730623",
                "8727393",
                "8720621",
                "8720357",
                "8720318",
                "8720063",
                "8720061",
                "8719909",
                "8719386",
                "8713622",
                "8712590",
            },
        )

    def test_get_alerts_returns_empty_when_no_match(self):
        response = self.client.get(
            self.url,
            {"from": "2023-01-01", "to": "2026-12-31", "disease": "Smallpox"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["alerts"], [])

    def test_get_alerts_default_window_uses_365_days(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_to = date.today()
        expected_from = expected_to - timedelta(days=365)

        self.assertEqual(response.data["from"], expected_from.isoformat())
        self.assertEqual(response.data["to"], expected_to.isoformat())

    def test_get_alerts_only_from_uses_today_as_to(self):
        response = self.client.get(self.url, {"from": "2026-02-01"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["from"], "2026-02-01")
        self.assertEqual(response.data["to"], date.today().isoformat())
