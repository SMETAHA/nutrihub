from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from .models import Recipe, RecipeIngredient
from .forms import RecipeForm
from products.models import FoodProduct
import json


def _parse_recipe_ingredients(raw):
    try:
        ingredients = json.loads(raw or "[]")
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(ingredients, list):
        return None
    parsed = []
    for ing in ingredients:
        if not isinstance(ing, dict):
            continue
        try:
            product_id = int(ing.get("product_id"))
            amount = float(ing.get("amount") or 0)
            piece_grams = float(ing.get("piece_grams") or 0)
        except (TypeError, ValueError):
            continue
        unit = ing.get("unit")
        if amount <= 0 or unit not in (RecipeIngredient.Unit.GRAM, RecipeIngredient.Unit.ML, RecipeIngredient.Unit.PCS):
            continue
        if not FoodProduct.objects.filter(id=product_id).exists():
            continue
        parsed.append({
            "product_id": product_id,
            "amount": amount,
            "unit": unit,
            "piece_grams": piece_grams,
        })
    return parsed

@login_required
def recipe_list(request):
    recipes = Recipe.objects.filter(created_by=request.user).order_by("-id")
    return render(request, "recipes/recipe_list.html", {"recipes": recipes})


@login_required
@transaction.atomic
def recipe_create(request):
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.created_by = request.user
            recipe.save()

            # Парсим ингредиенты из скрытого поля
            ingredients_raw = request.POST.get("ingredients_json", "[]")
            ingredients = _parse_recipe_ingredients(ingredients_raw)
            if ingredients is None:
                form.add_error(None, "Некорректный формат списка ингредиентов.")
                return render(request, "recipes/recipe_form.html", {"form": form, "ingredients_json": ingredients_raw})

            for ing in ingredients:
                RecipeIngredient.objects.create(recipe=recipe, **ing)
            return redirect("recipe_list")
    else:
        form = RecipeForm()
    return render(request, "recipes/recipe_form.html", {"form": form, "ingredients_json": "[]"})


@login_required
@transaction.atomic
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()

            # Очищаем старые ингредиенты
            recipe.ingredients.all().delete()

            ingredients_raw = request.POST.get("ingredients_json", "[]")
            ingredients = _parse_recipe_ingredients(ingredients_raw)
            if ingredients is None:
                form.add_error(None, "Некорректный формат списка ингредиентов.")
                return render(request, "recipes/recipe_form.html", {"form": form, "ingredients_json": ingredients_raw})

            for ing in ingredients:
                RecipeIngredient.objects.create(recipe=recipe, **ing)
            return redirect("recipe_list")
    else:
        form = RecipeForm(instance=recipe)
        # Готовим JSON для редактирования
        ingredients_json = json.dumps([
            {
                "product_id": i.product.id,
                "name": i.product.name,
                "brand": i.product.brand,
                "amount": i.amount,
                "unit": i.unit,
                "piece_grams": i.piece_grams,
                "kcal": i.product.calories_per_100g,
                "p": i.product.protein_per_100g,
                "f": i.product.fat_per_100g,
                "c": i.product.carbs_per_100g,
            }
            for i in recipe.ingredients.all()
        ])
    return render(request, "recipes/recipe_form.html", {"form": form, "ingredients_json": ingredients_json})


@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, created_by=request.user)
    if request.method == "POST":
        recipe.delete()
    return redirect("recipe_list")


# --- Поиск продуктов ---
@login_required
def api_products_search(request):
    q = request.GET.get("q", "").strip()
    qs = FoodProduct.objects.all()
    if q:
        parts = q.split()
        for part in parts:
            qs = qs.filter(Q(name__icontains=part) | Q(brand__icontains=part))
    data = [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "kcal": p.calories_per_100g,
            "p": p.protein_per_100g,
            "f": p.fat_per_100g,
            "c": p.carbs_per_100g,
        }
        for p in qs[:30]
    ]
    return JsonResponse({"results": data})
