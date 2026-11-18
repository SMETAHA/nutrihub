# core/utils.py
from datetime import date, timedelta
from math import log10

ACTIVITY_FACTORS = {
    'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9,
}

def clamp(x, lo, hi): return max(lo, min(hi, x))

def age_from_birthdate(birth_date):
    if not birth_date: return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

# --- BMR формулы ---
def bmr_mifflin(sex, weight_kg, height_cm, age_years):
    if None in (sex, weight_kg, height_cm, age_years): return None
    s = 5 if sex == 'male' else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age_years + s

def bmr_harris_benedict(sex, weight_kg, height_cm, age_years):
    if None in (sex, weight_kg, height_cm, age_years): return None
    if sex == 'male':
        return 66.47 + 13.75*weight_kg + 5.003*height_cm - 6.755*age_years
    else:
        return 655.1 + 9.563*weight_kg + 1.850*height_cm - 4.676*age_years

def estimate_bf_navy(sex, waist_cm=None, neck_cm=None, hip_cm=None, height_cm=None):
    # US Navy method (приблизительно; пригодится при отсутствии точного BF%)
    if None in (sex, waist_cm, neck_cm, height_cm): return None
    try:
        if sex == 'male':
            return 495 / (1.0324 - 0.19077*log10(waist_cm - neck_cm) + 0.15456*log10(height_cm)) - 450
        else:
            if hip_cm is None: return None
            return 495 / (1.29579 - 0.35004*log10(waist_cm + hip_cm - neck_cm) + 0.22100*log10(height_cm)) - 450
    except (ValueError, ZeroDivisionError):
        return None

def lean_body_mass(weight_kg, body_fat_percent):
    if weight_kg is None or body_fat_percent is None: return None
    return weight_kg * (1 - body_fat_percent/100.0)

def bmr_katch_mcardle(lean_mass_kg):
    return 370 + 21.6 * lean_mass_kg if lean_mass_kg is not None else None

def bmr_cunningham(lean_mass_kg):
    return 500 + 22 * lean_mass_kg if lean_mass_kg is not None else None

def tdee(bmr, activity_level):
    if not bmr: return None
    return bmr * ACTIVITY_FACTORS.get(activity_level or 'light', 1.375)

# ТЕF: ~10% от калорийности, учитываем отдельно (по желанию)
def thermic_effect(intake_kcal):
    return 0.1 * intake_kcal if intake_kcal is not None else 0

# NEAT-адаптация: чем больше дефицит, тем сильнее организм «жмётся»
def adaptive_neat_adjust(tdee_val, daily_deficit_kcal):
    if None in (tdee_val, daily_deficit_kcal): return 0
    # до ~20% TDEE снижаем NEAT до 5–8% линейно
    ratio = clamp(abs(daily_deficit_kcal)/tdee_val, 0, 0.2)
    return - tdee_val * ratio * 0.4  # 0..8% снижения

def daily_target_kcal(tdee_value, goal_type, weekly_delta_kg=0.5):
    if not tdee_value or not goal_type: return None
    delta_per_day = 7700 * weekly_delta_kg / 7  # 1 кг жира ≈ 7700 ккал
    if goal_type == 'lose':
        return tdee_value - delta_per_day
    elif goal_type == 'gain':
        return tdee_value + delta_per_day
    return tdee_value

def predict_goal_date(current_weight, target_weight, daily_deficit_kcal):
    if None in (current_weight, target_weight, daily_deficit_kcal) or daily_deficit_kcal == 0: return None
    kg_to_change = abs(target_weight - current_weight)
    if kg_to_change == 0: return None
    days = int(kg_to_change * 7700 / abs(daily_deficit_kcal))
    return date.today() + timedelta(days=days)

# EWMA-тренд (сглаживание веса или калорий)
def ewma(values, alpha=0.3):
    out = []
    m = None
    for v in values:
        m = v if m is None else (alpha*v + (1-alpha)*m)
        out.append(round(m, 2))
    return out

# Макроразклад: приоритет белка/жиров, остаток — угли
def macro_split(target_kcal, weight_kg, lean_mass_kg=None, mode='default'):
    if target_kcal is None or weight_kg is None: return None
    # Белок
    p_g = (2.0 if mode=='athlete' else 1.6) * (lean_mass_kg or weight_kg)
    # Жиры: минимум на гормоны
    f_g = max(0.6 * weight_kg, 40)
    # Остаток — угли
    p_kcal = p_g * 4
    f_kcal = f_g * 9
    c_kcal = max(target_kcal - p_kcal - f_kcal, 0)
    c_g = c_kcal / 4
    return {'protein_g': int(p_g), 'fat_g': int(f_g), 'carbs_g': int(c_g)}

# Автоподстройка на следующую неделю по тренду веса
def weekly_adjustment(target_weekly_delta_kg, actual_weekly_delta_kg):
    # 1 кг ~ 7700 ккал → в день ~ 1100 ккал/кг/нед
    delta_kg = (target_weekly_delta_kg or 0) - (actual_weekly_delta_kg or 0)
    return int(delta_kg * 7700 / 7)  # сколько ккал/день прибавить(+)/убавить(-)
