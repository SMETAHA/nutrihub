from django.contrib import admin
from django.urls import path, include
from core.views import home, dashboard, calculator, settings_view, macro_target_api

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('calculator/', calculator, name='calculator'),
    path('settings/', settings_view, name='settings'),
    path('accounts/', include('accounts.urls')),
    path('diary/', include('diary.urls')),
    path('products/', include('products.urls')),
    path('recipes/', include('recipes.urls')),
    path('feed/', include('socialfeed.urls')),
    path('dashboard/macro-target/', macro_target_api, name='macro_target_api'),
    path('api/', include('api.urls')),
]

