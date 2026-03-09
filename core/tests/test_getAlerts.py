from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class TestGetAlerts(APITestCase):

    fixtures = ["alerts.json"]

    def setUp(self):
        self.url = reverse("get-alerts")

    def test_get_alerts_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)