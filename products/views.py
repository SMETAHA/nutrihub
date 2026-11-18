from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import FoodProduct
from .forms import ProductForm
from diary.models import DiaryEntry
from rapidfuzz import process


def product_list(request):
    q = request.GET.get('q', '').strip()
    tag = request.GET.get('tag', '').strip()
    sort_by = request.GET.get('sort', '').strip()  # calories, protein, fat, carbs

    # Базовый запрос
    products_qs = FoodProduct.objects.filter(is_public=True)

    # Фильтр по тегу
    if tag:
        products_qs = products_qs.filter(tags__icontains=tag)

    # Fuzzy-поиск по названию, бренду и тегам
    if q:
        all_products = list(products_qs)
        names = [f"{p.name} {p.brand} {p.tags}" for p in all_products]
        matches = process.extract(q, names, limit=50, score_cutoff=50)
        matched_ids = [all_products[idx].id for _, _, idx in matches]
        products_qs = products_qs.filter(id__in=matched_ids)

    # Сортировка
    sort_map = {
        'calories': 'calories_per_100g',
        'protein': 'protein_per_100g',
        'fat': 'fat_per_100g',
        'carbs': 'carbs_per_100g',
    }
    if sort_by in sort_map:
        products_qs = products_qs.order_by(f"-{sort_map[sort_by]}")

    # Список уникальных тегов
    tag_list = (
        FoodProduct.objects.filter(is_public=True)
        .exclude(tags="")
        .values_list("tags", flat=True)
    )
    tags = sorted(set([t.strip() for s in tag_list for t in s.split(",") if t.strip()]))

    return render(request, "products/list.html", {
        "products": products_qs,
        "tags": tags,
        "selected_tag": tag,
        "query": q,
        "sort_by": sort_by,
    })
@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.created_by = request.user
            p.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'products/form.html', {'form': form})

@login_required
def quick_add_to_diary(request, pk):
    product = get_object_or_404(FoodProduct, pk=pk)
    grams = int(request.GET.get('g', 100))
    DiaryEntry.objects.create(user=request.user, product=product, grams=grams)
    return redirect('diary')

def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = request.POST.get('brand', '')
        calories = request.POST.get('calories_per_100g')
        protein = request.POST.get('protein_per_100g', 0)
        fat = request.POST.get('fat_per_100g', 0)
        carbs = request.POST.get('carbs_per_100g', 0)
        fiber = request.POST.get('fiber_per_100g', 0)
        sugar = request.POST.get('sugar_per_100g', 0)
        sodium = request.POST.get('sodium_mg_per_100g', 0)
        potassium = request.POST.get('potassium_mg_per_100g', 0)
        tags = request.POST.get('tags', '')

        FoodProduct.objects.create(
            name=name,
            brand=brand,
            calories_per_100g=calories,
            protein_per_100g=protein,
            fat_per_100g=fat,
            carbs_per_100g=carbs,
            fiber_per_100g=fiber,
            sugar_per_100g=sugar,
            sodium_mg_per_100g=sodium,
            potassium_mg_per_100g=potassium,
            tags=tags,
            created_by=request.user if request.user.is_authenticated else None
        )

        return redirect('product_list')

    return render(request, 'products/add_product.html')

@login_required
def api_search_products(request):
    q = (request.GET.get('q') or '').strip()
    qs = FoodProduct.objects.all().order_by('name')
    if q:
        qs = qs.filter(name__icontains=q)
    qs = qs[:50]
    return JsonResponse({
        "results": [
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand or "",
                "kcal": p.calories_per_100g or 0,
                "p": p.protein_per_100g or 0,
                "f": p.fat_per_100g or 0,
                "c": p.carbs_per_100g or 0,
            } for p in qs
        ]
    })