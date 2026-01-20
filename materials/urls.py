# materials/urls.py - ПОЛНАЯ ВЕРСИЯ
from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    # Основные страницы материалов
    path('', views.MaterialListView.as_view(), name='material_list'),
    path('create/', views.MaterialCreateView.as_view(), name='material_create'),
    path('<int:pk>/', views.MaterialDetailView.as_view(), name='material_detail'),
    path('<int:pk>/update/', views.MaterialUpdateView.as_view(), name='material_update'),
    path('<int:pk>/delete/', views.MaterialDeleteView.as_view(), name='material_delete'),

    # Рецепты материалов
    path('recipes/add/<int:product_id>/',
         views.material_recipe_create,
         name='add_recipe'),
    path('recipes/<int:pk>/update/',
         views.MaterialRecipeUpdateView.as_view(),
         name='materialrecipe_update'),
    path('recipes/<int:pk>/delete/',
         views.MaterialRecipeDeleteView.as_view(),
         name='materialrecipe_delete'),
    
    # Отчёты и аналитика
    path('report/', views.material_report, name='report'),
    path('low-stock/', views.LowStockAlertView.as_view(), name='low_stock'),
    path('reservations/', views.MaterialReservationsView.as_view(), name='reservations'),
    
    # Быстрые действия (AJAX)
    path('quick-add/', views.quick_add_material, name='quick_add'),
    path('<int:pk>/update-quantity/', views.update_material_quantity, name='update_quantity'),
    path('api/<int:pk>/info/', views.material_info_api, name='material_info_api'),
    path('api/materials/list/', views.materials_list_api, name='materials_list_api'),
    
    # Экспорт
    path('export-csv/', views.export_materials_csv, name='export_csv'),
]