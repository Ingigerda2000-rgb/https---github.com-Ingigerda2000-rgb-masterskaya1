from django.urls import path
from . import views

app_name = 'custom_orders'

urlpatterns = [
    # Многошаговый конструктор (6 шагов)
    path('constructor/', views.constructor_main, name='constructor_main'),
    path('constructor/step/<int:step>/', views.constructor_step, name='constructor_step'),
    path('constructor/step/<int:step>/<int:template_id>/', views.constructor_step, name='constructor_step_template'),
    path('constructor/save-step/', views.save_constructor_step, name='save_constructor_step'),
    path('constructor/finalize/', views.finalize_custom_order, name='finalize_custom_order'),
    
    # Старые URL для совместимости
    path('', views.custom_order_constructor, name='custom_order_constructor'),
    path('category/', views.choose_category, name='choose_category'),
    path('create/<int:product_id>/', views.custom_order_create, name='custom_order_create'),
    path('preview/<int:specification_id>/', views.custom_order_preview, name='custom_order_preview'),
    path('my-orders/', views.my_custom_orders, name='my_custom_orders'),
    path('calculate-price/', views.calculate_custom_price, name='calculate_custom_price'),
    
    # Для мастеров
    path('master/orders/', views.master_custom_orders, name='master_custom_orders'),
    path('master/edit/<int:specification_id>/', views.edit_custom_order, name='edit_custom_order'),
    path('master/approve/<int:specification_id>/', views.approve_custom_order, name='approve_custom_order'),
    path('master/reject/<int:specification_id>/', views.reject_custom_order, name='reject_custom_order'),
]
