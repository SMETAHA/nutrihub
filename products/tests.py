from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.db.models.deletion import ProtectedError

from diary.models import DiaryEntry
from products.models import FoodProduct


class ProductAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="StrongPass123!")
        self.other = User.objects.create_user(username="other", password="StrongPass123!")
        self.product = FoodProduct.objects.create(
            name="Овсянка",
            calories_per_100g=350,
            protein_per_100g=12,
            fat_per_100g=7,
            carbs_per_100g=60,
            created_by=self.owner,
            is_public=False,
        )

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

    def test_owner_can_edit_private_product(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("product_edit", args=[self.product.pk]),
            {
                "name": "Овсянка быстрого приготовления",
                "brand": "Test",
                "calories_per_100g": "360",
                "protein_per_100g": "13",
                "fat_per_100g": "7",
                "carbs_per_100g": "61",
                "fiber_per_100g": "10",
                "sugar_per_100g": "2",
                "sodium_mg_per_100g": "1",
                "potassium_mg_per_100g": "20",
                "tags": "завтрак",
                "is_public": "on",
            },
        )

        self.assertRedirects(response, reverse("product_list"))
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_public)
        self.assertEqual(self.product.name, "Овсянка быстрого приготовления")

    def test_other_user_cannot_edit_product(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("product_edit", args=[self.product.pk]))

        self.assertEqual(response.status_code, 404)

    def test_private_product_is_hidden_from_other_user(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("product_list"))

        self.assertNotContains(response, "Овсянка")

    def test_owner_can_delete_unused_product(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("product_delete", args=[self.product.pk]))

        self.assertRedirects(response, reverse("product_list"))
        self.assertFalse(FoodProduct.objects.filter(pk=self.product.pk).exists())

    def test_negative_nutrients_are_rejected(self):
        with self.assertRaises(ValidationError):
            FoodProduct.objects.create(
                name="Некорректный",
                calories_per_100g=-1,
                created_by=self.owner,
            )

    def test_product_used_by_diary_is_protected(self):
        entry = DiaryEntry.objects.create(
            user=self.owner,
            date="2026-11-18",
            time="12:00",
            meal="lunch",
            product=self.product,
            grams=100,
        )
        self.assertIsNotNone(entry.pk)

        with self.assertRaises(ProtectedError):
            self.product.delete()
