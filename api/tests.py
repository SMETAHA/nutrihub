from datetime import date, time

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from diary.models import DiaryEntry, PlannedMeal
from products.models import FoodProduct
from recipes.models import Recipe


class NutritionAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='api-owner', password='StrongPass123!')
        self.other = User.objects.create_user(username='api-other', password='StrongPass123!')
        self.token = Token.objects.create(user=self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.product = FoodProduct.objects.create(
            name='Творог',
            calories_per_100g=120,
            protein_per_100g=16,
            fat_per_100g=5,
            carbs_per_100g=3,
            created_by=self.owner,
            is_public=True,
        )

    def test_product_list_and_create(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Творог', str(response.data))

        response = self.client.post('/api/products/', {
            'name': 'Яйцо',
            'calories_per_100g': 143,
            'protein_per_100g': 13,
            'fat_per_100g': 11,
            'carbs_per_100g': 1,
            'is_public': False,
            'tags': 'яйца',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_by'], self.owner.pk)

    def test_product_owner_can_update_other_cannot(self):
        response = self.client.patch(
            f'/api/products/{self.product.pk}/',
            {'name': 'Творог обезжиренный'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=self.other).key}'
        )
        response = self.client.patch(
            f'/api/products/{self.product.pk}/',
            {'name': 'Чужая правка'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_negative_product_nutrients_are_rejected(self):
        response = self.client.post('/api/products/', {
            'name': 'Некорректный',
            'calories_per_100g': -10,
            'is_public': True,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recipe_create_with_nested_ingredients(self):
        response = self.client.post('/api/recipes/', {
            'name': 'Творожная смесь',
            'servings': 2,
            'instructions': 'Смешать',
            'is_public': True,
            'tags': 'завтрак',
            'ingredients': [{
                'product': self.product.pk,
                'amount': 200,
                'unit': 'g',
                'piece_grams': 0,
            }],
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(pk=response.data['id'])
        self.assertEqual(recipe.created_by, self.owner)
        self.assertEqual(recipe.ingredients.count(), 1)

    def test_diary_is_isolated_by_user(self):
        entry = DiaryEntry.objects.create(
            user=self.owner,
            date=date(2026, 11, 18),
            time=time(hour=12),
            meal='lunch',
            product=self.product,
            grams=100,
        )

        response = self.client.get('/api/diary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=self.other).key}'
        )
        response = self.client.get('/api/diary/')
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(f'/api/diary/{entry.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_diary_create_calculates_totals(self):
        response = self.client.post('/api/diary/', {
            'date': '2026-11-18',
            'time': '12:30:00',
            'meal': 'lunch',
            'product': self.product.pk,
            'grams': 150,
            'servings': 0,
            'note': 'обед',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_kcal'], 180)
        entry = DiaryEntry.objects.get(pk=response.data['id'])
        self.assertEqual(entry.user, self.owner)

    def test_planned_meal_create_and_owner_isolation(self):
        response = self.client.post('/api/planned-meals/', {
            'date': '2026-11-18',
            'time': '13:00:00',
            'meal_type': 'lunch',
            'product': self.product.pk,
            'grams': 200,
            'servings': 0,
            'note': 'запланировано',
            'done': False,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        meal = PlannedMeal.objects.get(pk=response.data['id'])
        self.assertEqual(meal.user, self.owner)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {Token.objects.create(user=self.other).key}'
        )
        response = self.client.get(f'/api/planned-meals/{meal.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_requires_authentication(self):
        self.client.credentials()
        response = self.client.get('/api/products/')
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
