from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ProductAccessTests(TestCase):
    def test_add_product_requires_login(self):
        response = self.client.get(reverse("add_product"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_product_creation_requires_post(self):
        User.objects.create_user(username="tester", password="StrongPass123!")
        self.client.login(username="tester", password="StrongPass123!")

        response = self.client.post(
            reverse("add_product"),
            {
                "name": "Продукт",
                "brand": "",
                "calories_per_100g": "100",
                "protein_per_100g": "10",
                "fat_per_100g": "5",
                "carbs_per_100g": "15",
                "fiber_per_100g": "2",
                "sugar_per_100g": "3",
                "sodium_mg_per_100g": "20",
                "potassium_mg_per_100g": "30",
                "tags": "test",
            },
        )

        self.assertEqual(response.status_code, 302)
