from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    # Регистрация и авторизация
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    
    # Выход из системы (кастомный view)
    path('logout/', views.custom_logout, name='logout'),
    
    # Подтверждение email
    path('confirm-email/<uidb64>/<token>/', views.confirm_email, name='confirm_email'),
    path('resend-confirmation/', views.resend_confirmation_email, name='resend_confirmation'),
    
    # Профиль пользователя
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
    
    # Функции мастера
    path('become-master/', views.become_master, name='become_master'),
    path('master-dashboard/', views.master_dashboard, name='master_dashboard'),
    path('masters/', views.master_list, name='master_list'),
    path('master/<int:user_id>/', views.master_detail, name='master_detail'),
    
    # Страница подтверждения выхода (GET запрос)
    path('logout-confirm/', TemplateView.as_view(template_name='accounts/logout.html'), name='logout_confirm'),
]