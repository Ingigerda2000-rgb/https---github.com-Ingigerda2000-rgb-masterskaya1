from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
   path('', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('checkout/', views.checkout, name='checkout'),
    # Маршрут apply-promo/ перенесен в приложение discounts
    path('<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('<int:order_id>/update-status-ajax/', views.update_order_status_ajax, name='update_order_status_ajax'),
    # Можно добавить позже:
    # path('<int:order_id>/payment/', views.process_payment, name='process_payment'),
]
