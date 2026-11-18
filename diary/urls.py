from django.urls import path
from . import views
urlpatterns = [

    path('planner/', views.planner_view, name='planner_view'),
    path('planner/add/', views.planner_add, name='planner_add'),
    path('planner/<int:pk>/toggle/', views.planner_toggle, name='planner_toggle'),
    path('planner/<int:pk>/delete/', views.planner_delete, name='planner_delete'),
    path('planner/day/<str:date>/', views.planner_day, name='planner_day'),
path('api/planner/transfer/<int:plan_id>/', views.planner_transfer, name='planner_transfer'),




    path('add-weight/', views.add_weight, name='add_weight'),

    path('entry/<int:pk>/grams/', views.update_entry_grams, name='update_entry_grams'),
    path('', views.diary_archive, name='diary_archive'),
    path('add/', views.diary_add, name='diary_add'),

    path('day/<str:day>/', views.diary_day_details, name='diary_day_details'),
    path('api/delete/<int:entry_id>/', views.delete_diary_entry_api, name='delete_diary_entry_api'),
    path('api/preview/', views.nutrition_preview, name='nutrition_preview'),
    path("api/get/<int:entry_id>/", views.api_get_entry, name="api_get_entry"),
    path('export/day/<str:day>/csv/', views.export_day_csv, name='export_day_csv'),
    path('export/day/<str:day>/pdf/', views.export_day_pdf, name='export_day_pdf'),
    path('export/day/<str:day>/md/', views.export_day_md, name='export_day_md'),
    path('export/month/<int:year>/<int:month>/csv/', views.export_month_csv, name='export_month_csv'),
    path('export/month/<int:year>/<int:month>/pdf/', views.export_month_pdf, name='export_month_pdf'),



]
