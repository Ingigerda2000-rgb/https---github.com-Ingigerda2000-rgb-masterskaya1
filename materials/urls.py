# materials/urls.py - ПОЛНАЯ ВЕРСИЯ
from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    # Основные страницы материалов
    path('', views.MaterialListView.as_view(), name='material_list'),
    path('create/', views.MaterialCreateView.as_view(), name='material_create'),
    path('<uuid:pk>/', views.MaterialDetailView.as_view(), name='material_detail'),
    path('<uuid:pk>/update/', views.MaterialUpdateView.as_view(), name='material_update'),
    path('<uuid:pk>/delete/', views.MaterialDeleteView.as_view(), name='material_delete'),
    
    # Рецепты материалов
    path('recipes/add/<uuid:product_id>/', 
         views.MaterialRecipeCreateView.as_view(), 
         name='add_recipe'),
    
    # Отчёты и аналитика
    path('report/', views.material_report, name='report'),
    path('low-stock/', views.LowStockAlertView.as_view(), name='low_stock'),
    path('reservations/', views.MaterialReservationsView.as_view(), name='reservations'),
    
    # Быстрые действия (AJAX)
    path('quick-add/', views.quick_add_material, name='quick_add'),
    path('<uuid:pk>/update-quantity/', views.update_material_quantity, name='update_quantity'),
    
    # Экспорт
    path('export-csv/', views.export_materials_csv, name='export_csv'),
]