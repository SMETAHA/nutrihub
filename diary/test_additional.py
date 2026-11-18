from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from diary.models import DiaryEntry, PlannedMeal
from products.models import FoodProduct
from recipes.models import Recipe
from socialfeed.models import Post


class NutritionFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="feature", password="StrongPass123!")
        self.other = User.objects.create_user(username="feature-other", password="StrongPass123!")
        self.product = FoodProduct.objects.create(
            name="Гречка",
            calories_per_100g=340,
            protein_per_100g=13,
            fat_per_100g=3,
            carbs_per_100g=65,
            is_public=True,
        )
        self.recipe = Recipe.objects.create(
            name="Гречка с овощами",
            servings=2,
            created_by=self.user,
            is_public=True,
        )
        self.client.force_login(self.user)

    def test_planner_create_list_and_transfer(self):
        response = self.client.post(reverse("planner_add"), {
            "date": "2026-11-18",
            "meal_type": "lunch",
            "time": "13:30",
            "category": "product",
            "item_id": str(self.product.pk),
            "grams": "150",
            "servings": "0",
            "note": "обед",
        })
        self.assertEqual(response.status_code, 302)

        planned = PlannedMeal.objects.get(user=self.user)
        self.assertEqual(planned.product, self.product)

        response = self.client.post(reverse("planner_transfer", args=[planned.pk]))
        self.assertEqual(response.status_code, 200)

        planned.refresh_from_db() if PlannedMeal.objects.filter(pk=planned.pk).exists() else None
        entry = DiaryEntry.objects.get(user=self.user)
        self.assertEqual(entry.product, self.product)
        self.assertEqual(entry.grams, 150)

    def test_recipe_owner_only_edit(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("recipe_edit", args=[self.recipe.pk]))

        self.assertEqual(response.status_code, 404)

    def test_recipe_creation_saves_owned_recipe(self):
        response = self.client.post(reverse("recipe_create"), {
            "name": "Новый рецепт",
            "servings": "2",
            "instructions": "Готовить",
            "tags": "ужин",
            "is_public": "on",
            "ingredients_json": "[]",
        })

        self.assertRedirects(response, reverse("recipe_list"))
        recipe = Recipe.objects.get(name="Новый рецепт")
        self.assertEqual(recipe.created_by, self.user)

    def test_export_day_csv_is_owned(self):
        DiaryEntry.objects.create(
            user=self.user,
            date=date(2026, 11, 18),
            time=time(hour=12),
            meal="lunch",
            product=self.product,
            grams=100,
        )
        response = self.client.get(reverse("export_day_csv", args=["2026-11-18"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(response, "Гречка")

    def test_export_does_not_include_other_users_entries(self):
        DiaryEntry.objects.create(
            user=self.other,
            date=date(2026, 11, 18),
            time=time(hour=12),
            meal="lunch",
            product=self.product,
            grams=100,
        )
        response = self.client.get(reverse("export_day_csv", args=["2026-11-18"]))

        self.assertNotContains(response, "Гречка")

    def test_feed_shows_own_post(self):
        Post.objects.create(user=self.user, text="Сегодня лёгкий день")

        response = self.client.get(reverse("feed"))

        self.assertContains(response, "Сегодня лёгкий день")

    def test_private_recipe_not_shown_in_user_recipe_list(self):
        private_recipe = Recipe.objects.create(
            name="Секретный рецепт",
            servings=1,
            created_by=self.other,
            is_public=False,
        )

        response = self.client.get(reverse("recipe_list"))

        self.assertNotContains(response, private_recipe.name)
