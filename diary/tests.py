from datetime import date, time

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from diary.models import DiaryEntry, PlannedMeal
from products.models import FoodProduct
from recipes.models import Recipe


class DiaryIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="StrongPass123!")
        self.product = FoodProduct.objects.create(
            name="Овсянка",
            calories_per_100g=350,
            protein_per_100g=12,
            fat_per_100g=7,
            carbs_per_100g=60,
        )

    def test_product_entry_calculates_nutrients(self):
        entry = DiaryEntry.objects.create(
            user=self.user,
            date=date.today(),
            time=time(hour=12),
            meal="lunch",
            product=self.product,
            grams=100,
        )

        self.assertEqual(entry.total_kcal, 350)
        self.assertEqual(entry.total_protein, 12)
        self.assertEqual(entry.total_fat, 7)
        self.assertEqual(entry.total_carbs, 60)

    def test_entry_requires_exactly_one_source(self):
        with self.assertRaises(ValidationError):
            DiaryEntry.objects.create(
                user=self.user,
                date=date.today(),
                time=time(hour=12),
                meal="lunch",
                grams=100,
            )

        recipe = Recipe.objects.create(name="Каша", servings=1, created_by=self.user)
        with self.assertRaises(ValidationError):
            DiaryEntry.objects.create(
                user=self.user,
                date=date.today(),
                time=time(hour=12),
                meal="lunch",
                product=self.product,
                recipe=recipe,
                grams=100,
            )

    def test_negative_grams_are_rejected(self):
        with self.assertRaises(ValidationError):
            DiaryEntry.objects.create(
                user=self.user,
                date=date.today(),
                time=time(hour=12),
                meal="lunch",
                product=self.product,
                grams=-1,
            )

    def test_planned_meal_requires_exactly_one_source(self):
        with self.assertRaises(ValidationError):
            PlannedMeal.objects.create(
                user=self.user,
                date=date.today(),
                time=time(hour=12),
                meal_type="lunch",
                grams=100,
            )

    def test_update_entry_grams_enforces_ownership(self):
        entry = DiaryEntry.objects.create(
            user=self.user,
            date=date.today(),
            time=time(hour=12),
            meal="lunch",
            product=self.product,
            grams=100,
        )
        other = User.objects.create_user(username="other", password="StrongPass123!")

        self.client.force_login(other)
        response = self.client.post(
            reverse("update_entry_grams", args=[entry.pk]),
            {"grams": "50"},
        )

        self.assertEqual(response.status_code, 404)

    def test_quick_add_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("product_quick_add", args=[self.product.pk]),
        )

        self.assertEqual(response.status_code, 405)
