from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from diary.models import DiaryEntry ,WeightLog
from accounts.models import Profile
from core.utils import age_from_birthdate, bmr_mifflin, tdee, daily_target_kcal, predict_goal_date, weekly_adjustment, \
    ewma
from core.utils import macro_split
from django.http import JsonResponse
from core.utils import (age_from_birthdate, bmr_mifflin, bmr_harris_benedict,
    bmr_katch_mcardle, bmr_cunningham, tdee, daily_target_kcal,
    lean_body_mass, macro_split, thermic_effect, adaptive_neat_adjust)

def home(request):
    return render(request, 'core/home.html')

@login_required
def dashboard(request):

    today = date.today()
    last7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
    entries = DiaryEntry.objects.filter(user=request.user, date__in=last7).select_related('product')
    kcal_by_day = {d:0 for d in last7}
    protein_by_day = {d:0 for d in last7}
    fat_by_day = {d:0 for d in last7}
    carbs_by_day = {d:0 for d in last7}
    for e in entries:
        kcal_by_day[e.date] += e.total_kcal
        protein_by_day[e.date] += e.total_protein
        fat_by_day[e.date] += e.total_fat
        carbs_by_day[e.date] += e.total_carbs

    dates = [d.strftime('%d.%m') for d in last7]
    kcal_vals = [kcal_by_day[d] for d in last7]
    protein_vals = [protein_by_day[d] for d in last7]
    fat_vals = [fat_by_day[d] for d in last7]
    carbs_vals = [carbs_by_day[d] for d in last7]

    profile = Profile.objects.filter(user=request.user).first()
    bmr = tdee_val = target = goal_eta = None
    if profile:
        age = age_from_birthdate(profile.birth_date)
        bmr = bmr_mifflin(profile.sex, profile.current_weight_kg or profile.start_weight_kg, profile.height_cm, age)
        tdee_val = tdee(bmr, profile.activity_level)
        target = daily_target_kcal(tdee_val, profile.goal_type, weekly_delta_kg=profile.weekly_delta_kg or 0.5)
        if profile.target_weight_kg and profile.current_weight_kg and target and tdee_val:
            deficit = target - tdee_val
            goal_eta = predict_goal_date(profile.current_weight_kg, profile.target_weight_kg, deficit)

    context = {
        'dates': dates,
        'kcal_vals': kcal_vals,
        'protein_vals': protein_vals,
        'fat_vals': fat_vals,
        'carbs_vals': carbs_vals,
        'bmr': bmr, 'tdee_val': tdee_val, 'target_kcal': target, 'goal_eta': goal_eta,
        'today_entries': DiaryEntry.objects.filter(user=request.user, date=today),
    }
    # core/views.py (внутри dashboard)
    weights_qs = WeightLog.objects.filter(user=request.user).order_by('date')[:30]
    w_dates = [w.date.strftime('%d.%m') for w in weights_qs]
    w_vals = [float(w.weight) for w in weights_qs]
    w_trend = ewma(w_vals, alpha=0.4) if w_vals else []

    # фактическая скорость за 7 дней
    actual_weekly = None
    if len(w_trend) >= 8:
        actual_weekly = w_trend[-1] - w_trend[-8]
    left_kcal = None
    if target and kcal_vals:
        left_kcal = int(target - kcal_vals[-1])

    adj = None
    if profile and profile.goal_type in ('lose', 'gain') and actual_weekly is not None:
        target_weekly = (-profile.weekly_delta_kg) if profile.goal_type == 'lose' else (profile.weekly_delta_kg)
        adj = weekly_adjustment(target_weekly, actual_weekly)

    context.update({
        'w_dates': w_dates, 'w_vals': w_vals, 'w_trend': w_trend, 'kcal_adjust_next_week': adj
    })
    context.update({'left_kcal': left_kcal})

    return render(request, 'core/dashboard.html', context)

def _safe_int(v, default=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default

def _safe_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def _normalize_sex(v):
    if not v:
        return None
    v = str(v).strip().lower()
    if v in ('male', 'м', 'муж', 'мужской'):
        return 'male'
    if v in ('female', 'ж', 'жен', 'женский'):
        return 'female'
    return None

@login_required
def calculator(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    result = None

    # значения для формы по умолчанию
    initial_age = profile.age() or 25
    selected_method = 'mifflin'

    if request.method == 'POST':
        # --- читаем и нормализуем входные поля ---
        selected_method = request.POST.get('bmr_method', 'mifflin')
        sex = _normalize_sex(request.POST.get('sex') or profile.sex)
        height_cm = _safe_int(request.POST.get('height_cm'), profile.height_cm)
        weight_kg = _safe_float(
            request.POST.get('weight_kg'),
            profile.current_weight_kg or profile.start_weight_kg
        )
        age = _safe_int(request.POST.get('age'), initial_age)
        activity = (request.POST.get('activity_level') or profile.activity_level or 'light').strip()
        goal_type = (request.POST.get('goal_type') or profile.goal_type or 'maintain').strip()
        weekly_delta = _safe_float(request.POST.get('weekly_delta_kg'), profile.weekly_delta_kg or 0.5)

        # --- считаем BMR по выбранному методу ---
        BMR = None
        if selected_method == 'harris':
            BMR = bmr_harris_benedict(sex, weight_kg, height_cm, age)
        elif selected_method == 'katch':
            lm = profile.lean_mass()
            BMR = bmr_katch_mcardle(lm)
        elif selected_method == 'cunningham':
            lm = profile.lean_mass()
            BMR = bmr_cunningham(lm)
        else:
            BMR = bmr_mifflin(sex, weight_kg, height_cm, age)

        TDEE = tdee(BMR, activity) if BMR is not None else None
        target = daily_target_kcal(TDEE, goal_type, weekly_delta) if TDEE is not None else None

        # аккуратно считаем корректировку NEAT только если всё есть
        target_real = None
        if target is not None and TDEE is not None:
            adj_neat = adaptive_neat_adjust(TDEE, target - TDEE)
            target_real = int(target + adj_neat)

        macros = None
        if (target_real or target) and weight_kg:
            try:
                macros = macro_split(target_real or target, weight_kg, profile.lean_mass(), mode=getattr(profile, 'macro_mode', 'default'))
            except (TypeError, ValueError, ZeroDivisionError):
                macros = None

        # собираем результат
        result = {
            'BMR': int(BMR) if isinstance(BMR, (int, float)) else None,
            'TDEE': int(TDEE) if isinstance(TDEE, (int, float)) else None,
            'target': int(target) if isinstance(target, (int, float)) else None,
            'target_real': int(target_real) if isinstance(target_real, (int, float)) else None,
            'macros': macros
        }

        # сохранение в профиль по кнопке
        if 'save' in request.POST:
            if sex: profile.sex = sex
            if height_cm: profile.height_cm = height_cm
            if weight_kg: profile.current_weight_kg = weight_kg
            if activity: profile.activity_level = activity
            if goal_type: profile.goal_type = goal_type
            if weekly_delta is not None: profile.weekly_delta_kg = weekly_delta
            profile.save()
            return redirect('dashboard')

    context = {
        'profile': profile,
        'result': result,
        'age': initial_age,
        'selected_method': selected_method
    }
    return render(request, 'core/calculator.html', context)

@login_required
def settings_view(request):
    from accounts.forms import ProfileForm
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            request.session['theme'] = form.cleaned_data.get('theme', 'auto')
            return redirect('settings')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'core/settings.html', {'form': form})

@login_required
def macro_target_api(request):
    from accounts.models import Profile
    p = Profile.objects.filter(user=request.user).first()
    if not p: return JsonResponse({'protein_g':0,'fat_g':0,'carbs_g':0})
    target = p.tdee_target()
    lm = p.lean_mass()
    macros = macro_split(target, p.current_weight_kg or p.start_weight_kg, lm, mode=p.macro_mode or 'default')
    return JsonResponse(macros or {'protein_g':0,'fat_g':0,'carbs_g':0})