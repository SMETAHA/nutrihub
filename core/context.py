from datetime import date
from diary.models import DiaryEntry, WeightLog
from accounts.models import Profile

def theme_and_progress(request):
    theme = request.session.get('theme', 'auto')
    progress = 0
    tdee_target = None
    if request.user.is_authenticated:
        today = date.today()
        entries = DiaryEntry.objects.filter(user=request.user, date=today)
        total_kcal = sum(e.total_kcal for e in entries)
        try:
            profile = Profile.objects.get(user=request.user)
            tdee_target = profile.tdee_target()
            if tdee_target:
                progress = min(100, int(total_kcal / tdee_target * 100))
        except Profile.DoesNotExist:
            pass
    return {'theme': theme, 'top_progress_percent': progress, 'tdee_target': tdee_target}
