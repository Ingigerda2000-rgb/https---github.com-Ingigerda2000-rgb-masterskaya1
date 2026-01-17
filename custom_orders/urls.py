from django.urls import path
from . import views

app_name = 'custom_orders'

urlpatterns = [
    # Для покупателей
    path('', views.custom_order_constructor, name='custom_order_constructor'),
    path('create/<int:product_id>/', views.custom_order_create, name='custom_order_create'),
    path('preview/<int:specification_id>/', views.custom_order_preview, name='custom_order_preview'),
    path('my-orders/', views.my_custom_orders, name='my_custom_orders'),
    path('calculate-price/', views.calculate_custom_price, name='calculate_custom_price'),
    
    # Для мастеров
    path('master/orders/', views.master_custom_orders, name='master_custom_orders'),
    path('master/approve/<int:specification_id>/', views.approve_custom_order, name='approve_custom_order'),
    path('master/reject/<int:specification_id>/', views.reject_custom_order, name='reject_custom_order'),
]