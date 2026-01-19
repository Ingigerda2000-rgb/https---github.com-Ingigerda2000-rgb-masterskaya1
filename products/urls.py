from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('add/', views.add_product, name='add_product'),
    path('<int:product_id>/edit/', views.update_product, name='update_product'),
    path('favorite/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorite/check/<int:product_id>/', views.check_favorite, name='check_favorite'),
    path('favorites/', views.favorites_list, name='favorites_list'),
]
