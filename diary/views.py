import calendar
import csv
from django.core.exceptions import ValidationError

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from .models import DiaryEntry, PlannedMeal
from .forms import DiaryEntryForm, WeightLogForm
from products.models import FoodProduct
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST, require_http_methods
from recipes.models import Recipe
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

@login_required
def diary_view(request):
    # 📅 Текущая дата или дата из GET
    today_str = request.GET.get('date')
    today = date.fromisoformat(today_str) if today_str else date.today()

    # 📥 Обработка формы добавления записи
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect(f'/diary/?date={today.isoformat()}')
    else:
        form = DiaryEntryForm()

    # 🗂️ Получение записей за день (продукты и блюда)
    entries = (
        DiaryEntry.objects
        .filter(user=request.user, date=today)
        .select_related('product', 'recipe')
        .order_by('time')
    )

    # 📊 Суммарные показатели за день
    total_kcal = sum(e.total_kcal for e in entries)
    total_p = sum(e.total_protein for e in entries)
    total_f = sum(e.total_fat for e in entries)
    total_c = sum(e.total_carbs for e in entries)

    # ⚖️ Форма веса (если планируешь трекать динамику)
    weight_form = WeightLogForm()

    return render(request, 'diary/diary.html', {
        'form': form,
        'entries': entries,
        'day': today,
        'totals': {
            'kcal': total_kcal,
            'p': total_p,
            'f': total_f,
            'c': total_c
        },
        'weight_form': weight_form
    })

@login_required
def add_weight(request):
    if request.method == 'POST':
        form = WeightLogForm(request.POST)
        if form.is_valid():
            w = form.save(commit=False)
            w.user = request.user
            w.save()
    return redirect('diary')


@login_required
@require_POST
def update_entry_grams(request, pk):
    e = DiaryEntry.objects.filter(pk=pk, user=request.user).first()
    if not e: return JsonResponse({'ok': False}, status=404)
    try:
        grams = float(request.POST.get('grams'))
        if grams < 0:
            raise ValueError
        e.grams = grams
        e.save()
        return JsonResponse({'ok': True, 'kcal': e.total_kcal, 'p': e.total_protein, 'f': e.total_fat, 'c': e.total_carbs})
    except (TypeError, ValueError, ValidationError):
        return JsonResponse({'ok': False}, status=400)

@login_required
def diary_archive(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.itermonthdates(year, month)

    # Собираем записи по дням
    entries_by_day = {}
    entries = DiaryEntry.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )
    for e in entries:
        total = entries_by_day.get(e.date, 0)
        entries_by_day[e.date] = total + e.total_kcal

    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'month_days': month_days,
        'entries_by_day': entries_by_day,
        'today': today,
    }
    return render(request, 'diary/archive.html', context)


from recipes.models import Recipe

@login_required
def diary_add(request):
    if request.method == "POST":
        # 🗓 Чтение даты из формы
        date_str = request.POST.get("date")
        try:
            entry_date = date.fromisoformat(date_str) if date_str else date.today()
        except ValueError:
            entry_date = date.today()

        time_str  = request.POST.get("time") or "12:00"
        meal      = request.POST.get("meal") or "breakfast"
        category  = request.POST.get("category")
        item_id   = request.POST.get("item_id")
        try:
            grams = float(request.POST.get("grams") or 0)
            servings = float(request.POST.get("servings") or 0)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Некорректный вес или количество порций."}, status=400)
        if grams < 0 or servings < 0:
            return JsonResponse({"error": "Вес и количество порций не могут быть отрицательными."}, status=400)
        note      = request.POST.get("note") or ""

        try:
            t = datetime.strptime(time_str, "%H:%M").time()
        except (TypeError, ValueError):
            return JsonResponse({"error": "Некорректное время."}, status=400)

        entry = DiaryEntry(
            user=request.user,
            date=entry_date,
            time=t,
            meal=meal,
            note=note,
        )
        if category == "product":
            try:
                product = get_object_or_404(FoodProduct, id=int(item_id), is_public=True)
            except (TypeError, ValueError):
                return JsonResponse({"error": "Некорректный продукт."}, status=400)
            entry.product = product
            entry.grams = grams
        elif category == "recipe":
            try:
                recipe = get_object_or_404(Recipe, id=int(item_id), created_by=request.user)
            except (TypeError, ValueError):
                return JsonResponse({"error": "Некорректный рецепт."}, status=400)
            entry.recipe = recipe
            entry.grams = grams
            entry.servings = servings

        entry.full_clean()
        entry.save()
        return redirect("diary_archive")

    # 📅 Если GET — подставляем дату из параметра ?date
    date_str = request.GET.get("date")
    try:
        default_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        default_date = date.today()

    products = FoodProduct.objects.all().order_by("name")
    recipes  = Recipe.objects.filter(created_by=request.user).order_by("name")

    return render(
        request,
        "diary/add_entry.html",
        {
            "products": products,
            "recipes": recipes,
            "default_date": default_date,
        }
    )

@login_required
def nutrition_preview(request):
    """AJAX-предпросмотр БЖУ/ккал без сохранения."""
    cat = request.GET.get("category")
    item_id = request.GET.get("item_id")
    grams = float(request.GET.get("grams") or 0)
    servings = float(request.GET.get("servings") or 0)

    kcal=protein=fat=carbs=0.0

    if cat == "product" and item_id:
        p = get_object_or_404(FoodProduct, id=item_id)
        kcal    = p.calories_per_100g    * grams / 100.0
        protein = p.protein_per_100g * grams / 100.0
        fat     = p.fat_per_100g     * grams / 100.0
        carbs   = p.carbs_per_100g   * grams / 100.0

    elif cat == "recipe" and item_id:
        r = get_object_or_404(Recipe, id=item_id)
        if servings > 0:
            base = max(r.servings, 1e-9)
            kcal    = r.total_kcal    * servings / base
            protein = r.total_protein * servings / base
            fat     = r.total_fat     * servings / base
            carbs   = r.total_carbs   * servings / base
        else:
            tw = max(r.total_weight, 1e-9)
            kcal    = r.total_kcal    * grams / tw
            protein = r.total_protein * grams / tw
            fat     = r.total_fat     * grams / tw
            carbs   = r.total_carbs   * grams / tw

    return JsonResponse({
        "kcal": round(kcal,1),
        "protein": round(protein,1),
        "fat": round(fat,1),
        "carbs": round(carbs,1)
    })

@login_required
def diary_day_details(request, day):
    try:
        day_date = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        return redirect(f"/diary/?date={date.today().isoformat()}")

    # 🥗 Фактические приёмы
    entries = DiaryEntry.objects.filter(user=request.user, date=day_date).order_by('time')

    total_kcal = sum(e.total_kcal for e in entries)
    total_protein = sum(e.total_protein for e in entries)
    total_fat = sum(e.total_fat for e in entries)
    total_carbs = sum(e.total_carbs for e in entries)

    # 📝 План на день
    planned_meals = PlannedMeal.objects.filter(user=request.user, date=day_date).order_by('time')
    planned_totals = {
        'kcal': sum(m.total_kcal for m in planned_meals),
        'p': sum(m.total_protein for m in planned_meals),
        'f': sum(m.total_fat for m in planned_meals),
        'c': sum(m.total_carbs for m in planned_meals),
    }

    return render(request, 'diary/day_details.html', {
        'entries': entries,
        'day': day_date,
        'totals': {
            'kcal': total_kcal,
            'p': total_protein,
            'f': total_fat,
            'c': total_carbs
        },
        'planned_meals': planned_meals,
        'planned_totals': planned_totals
    })

@login_required
def api_get_entry(request, entry_id):
    entry = DiaryEntry.objects.get(id=entry_id, user=request.user)
    return JsonResponse({
        "grams": entry.grams,
        "time": entry.time.strftime("%H:%M")
    })



@login_required
def delete_diary_entry_api(request, entry_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Only DELETE allowed'}, status=405)
    entry = get_object_or_404(DiaryEntry, id=entry_id, user=request.user)
    entry.delete()
    return JsonResponse({'success': True})



import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from .models import DiaryEntry

# 📌 Регистрируем шрифт с поддержкой кириллицы (один раз)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))


@login_required
def export_day_csv(request, day):
    """Экспорт дневника за один день в CSV (UTF-8 BOM для Excel)."""
    entries = DiaryEntry.objects.filter(user=request.user, date=day)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="diary_{day}.csv"'
    response.write('\ufeff')  # 👈 BOM

    writer = csv.writer(response)
    writer.writerow(['Время', 'Название', 'Вес (г)', 'Ккал', 'Б', 'Ж', 'У'])
    for e in entries:
        name = e.product.name if e.product else (e.recipe.name if e.recipe else "—")
        writer.writerow([
            e.time,
            name,
            round(e.grams, 1),
            round(e.total_kcal, 1),
            round(e.total_protein, 1),
            round(e.total_fat, 1),
            round(e.total_carbs, 1)
        ])
    return response


@login_required
def export_month_csv(request, year, month):
    """Экспорт дневника за месяц в CSV (UTF-8 BOM)."""
    entries = DiaryEntry.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).order_by('date')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="diary_{year}_{month}.csv"'
    response.write('\ufeff')  # 👈 BOM

    writer = csv.writer(response)
    writer.writerow(['Дата', 'Время', 'Название', 'Вес (г)', 'Ккал', 'Б', 'Ж', 'У'])
    for e in entries:
        name = e.product.name if e.product else (e.recipe.name if e.recipe else "—")
        writer.writerow([
            e.date,
            e.time,
            name,
            round(e.grams, 1),
            round(e.total_kcal, 1),
            round(e.total_protein, 1),
            round(e.total_fat, 1),
            round(e.total_carbs, 1)
        ])
    return response


@login_required
def export_day_pdf(request, day):
    """Экспорт дневника за один день в PDF с поддержкой кириллицы."""
    entries = DiaryEntry.objects.filter(user=request.user, date=day)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="diary_{day}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("STSong-Light", 12)

    p.drawString(80, 820, f"Дневник питания — {day}")
    y = 790

    for e in entries:
        name = e.product.name if e.product else (e.recipe.name if e.recipe else "—")
        line = f"{e.time} | {name} | {round(e.grams)} г | {round(e.total_kcal)} ккал | Б {round(e.total_protein)} | Ж {round(e.total_fat)} | У {round(e.total_carbs)}"
        wrapped_lines = wrap_pdf_line(line, 90)
        for l in wrapped_lines:
            p.drawString(60, y, l)
            y -= 18
            if y < 60:
                p.showPage()
                p.setFont("STSong-Light", 12)
                y = 820

    p.showPage()
    p.save()
    return response


@login_required
def export_month_pdf(request, year, month):
    """Экспорт дневника за месяц в PDF с поддержкой кириллицы."""
    entries = DiaryEntry.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).order_by('date')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="diary_{year}_{month}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("STSong-Light", 12)

    p.drawString(80, 820, f"Дневник питания — {month}/{year}")
    y = 790

    for e in entries:
        name = e.product.name if e.product else (e.recipe.name if e.recipe else "—")
        line = f"{e.date} {e.time} | {name} | {round(e.grams)} г | {round(e.total_kcal)} ккал | Б {round(e.total_protein)} | Ж {round(e.total_fat)} | У {round(e.total_carbs)}"
        wrapped_lines = wrap_pdf_line(line, 90)
        for l in wrapped_lines:
            p.drawString(60, y, l)
            y -= 18
            if y < 60:
                p.showPage()
                p.setFont("STSong-Light", 12)
                y = 820

    p.showPage()
    p.save()
    return response


def wrap_pdf_line(text, max_chars=90):
    """Перенос длинных строк в PDF, чтобы кириллица не обрезалась."""
    lines = []
    while len(text) > max_chars:
        cut = text[:max_chars]
        # стараемся переносить по пробелу
        space_index = cut.rfind(' ')
        if space_index == -1:
            space_index = max_chars
        lines.append(text[:space_index])
        text = text[space_index:].lstrip()
    lines.append(text)
    return lines

@login_required
def export_day_md(request, day):
    """Экспорт дневника за один день в Markdown."""
    entries = DiaryEntry.objects.filter(user=request.user, date=day)
    lines = [f"# Дневник питания — {day}", ""]
    lines.append("| Время | Название | Вес (г) | Ккал | Б | Ж | У |")
    lines.append("|-------|-----------|--------|-------|---|---|---|")
    for e in entries:
        name = e.product.name if e.product else (e.recipe.name if e.recipe else "—")
        lines.append(f"| {e.time} | {name} | {e.grams} | {round(e.total_kcal)} | {round(e.total_protein)} | {round(e.total_fat)} | {round(e.total_carbs)} |")
    text = "\n".join(lines)
    response = HttpResponse(text, content_type='text/markdown; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="diary_{day}.md"'
    return response


def _parse_iso_date(s: str | None) -> date:
    """Парсим ISO YYYY-MM-DD, иначе возвращаем сегодня."""
    if not s:
        return date.today()
    try:
        return datetime.fromisoformat(s).date()   # ожидаем ISO
    except (TypeError, ValueError):
        return date.today()


@login_required
def planner_view(request):
    from datetime import date, datetime
    date_str = request.GET.get("date")
    if date_str:
        try:
            planner_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            planner_date = date.today()
    else:
        planner_date = date.today()  # ✅ если не передано — ставим сегодняшнюю

    products = FoodProduct.objects.all().order_by("name")
    recipes = Recipe.objects.filter(created_by=request.user).order_by("name")
    planned_meals = PlannedMeal.objects.filter(user=request.user, date=planner_date).order_by("time")

    return render(request, "planner/planner.html", {
        "planner_date": planner_date,
        "products": products,
        "recipes": recipes,
        "planned_meals": planned_meals
    })



@login_required
def planner_add(request):
    if request.method != "POST":
        return redirect("planner_view")

    date_str = request.POST.get("date")
    try:
        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return JsonResponse({"error": "Некорректная дата."}, status=400)

    meal_type = request.POST.get("meal_type")
    time_str  = request.POST.get("time")
    category  = request.POST.get("category")
    item_id   = request.POST.get("item_id")
    try:
        grams = float(request.POST.get("grams") or 0)
        servings = float(request.POST.get("servings") or 0)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Некорректный вес или количество порций."}, status=400)
    if grams < 0 or servings < 0:
        return JsonResponse({"error": "Вес и количество порций не могут быть отрицательными."}, status=400)
    note      = request.POST.get("note") or ""

    product = recipe = None
    if category == "product" and item_id:
        product = get_object_or_404(FoodProduct, id=item_id)
    elif category == "recipe" and item_id:
        recipe = get_object_or_404(Recipe, id=item_id, created_by=request.user)

    try:
        meal_time = datetime.strptime(time_str, "%H:%M").time()
    except (TypeError, ValueError):
        return JsonResponse({"error": "Некорректное время."}, status=400)

    PlannedMeal.objects.create(
        user=request.user,
        date=current_date,
        time=meal_time,
        meal_type=meal_type,
        product=product,
        recipe=recipe,
        grams=grams,
        servings=servings,
        note=note
    )
    return redirect(f"/diary/planner/?date={current_date.isoformat()}")




@login_required
@require_POST
def planner_toggle(request, pk):
    meal = get_object_or_404(PlannedMeal, pk=pk, user=request.user)
    meal.done = not meal.done
    meal.save()
    return JsonResponse({"status": "ok", "done": meal.done})


@login_required
@require_POST
def planner_delete(request, pk):
    meal = get_object_or_404(PlannedMeal, pk=pk, user=request.user)
    meal.delete()
    return JsonResponse({"status": "ok"})


@login_required
def planner_day(request, date):
    meals = PlannedMeal.objects.filter(user=request.user, date=date)
    data = [
        {
            "id": m.id,
            "time": m.time.strftime("%H:%M"),
            "name": m.name,
            "kcal": round(m.kcal),
            "done": m.done
        }
        for m in meals
    ]
    return JsonResponse(data, safe=False)




@login_required
def planner_transfer(request, plan_id):
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'error': 'Only DELETE or POST allowed'}, status=405)

    planned = get_object_or_404(PlannedMeal, id=plan_id, user=request.user)

    entry = DiaryEntry.objects.create(
        user=request.user,
        date=planned.date,
        time=planned.time,
        meal=planned.meal_type,
        product=planned.product,
        recipe=planned.recipe,
        grams=planned.grams,
        servings=planned.servings,
        note=f"[План] {planned.note or ''}"
    )

    planned.delete()

    return JsonResponse({
        'success': True,
        'id': entry.id,
        'time': entry.time.strftime("%H:%M"),
        'name': entry.product.name if entry.product else entry.recipe.name if entry.recipe else "—",
        'grams': entry.grams,
        'kcal': round(entry.total_kcal),
        'protein': round(entry.total_protein),
        'fat': round(entry.total_fat),
        'carbs': round(entry.total_carbs),
        'delete_url': f"/diary/api/delete/{entry.id}/"
    })



