from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Основные маршруты
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Отмена заказа
    path('<int:pk>/cancel/', views.OrderCancelView.as_view(), name='cancel_order'),
    
    # Управление статусами (для мастера/администратора)
    path('<int:pk>/update-status/', views.OrderStatusUpdateView.as_view(), name='update_order_status'),
    path('<int:pk>/timeline/', views.OrderTimelineView.as_view(), name='order_timeline'),
    
    # Для мастера
    path('master/', views.MasterOrdersView.as_view(), name='master_orders'),
    
    # AJAX методы
    path('<int:pk>/update-status-ajax/', views.update_order_status_ajax, name='update_status_ajax'),
    path('api/status-counts/', views.order_status_counts_api, name='status_counts_api'),
    
    # Оформление заказа (существующее - проверить наличие)
    # path('checkout/', views.checkout, name='checkout'),
]