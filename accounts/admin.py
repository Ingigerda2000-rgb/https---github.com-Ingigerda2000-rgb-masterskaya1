from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User
from django.contrib import messages

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Убираем поле username
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'phone', 'avatar', 'role')
        }),
        (_('Адрес'), {
            'fields': ('default_address', 'default_city', 'default_postal_code')
        }),
        (_('Для мастеров'), {
            'fields': ('master_bio', 'master_specialization', 'master_experience_years', 'master_rating'),
            'classes': ('collapse',)
        }),
        (_('Предпочтения'), {
            'fields': ('newsletter_subscription', 'email_confirmed')
        }),
        (_('Права доступа'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    # Обновленный list_display с email_confirmed
    list_display = ('email', 'first_name', 'last_name', 'role', 'email_confirmed', 'is_staff', 'created_at')
    
    # Добавляем фильтр для email_confirmed
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role', 'email_confirmed', 'created_at')
    
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')
    filter_horizontal = ('groups', 'user_permissions',)
    
    # Действия в админке
    actions = ['confirm_selected_emails', 'resend_confirmation_email']
    
    def confirm_selected_emails(self, request, queryset):
        """Подтвердить выбранные emails в админке"""
        updated = queryset.update(email_confirmed=True)
        self.message_user(request, f'Подтверждено {updated} email(s).', messages.SUCCESS)
    confirm_selected_emails.short_description = "Подтвердить выбранные emails"
    
    def resend_confirmation_email(self, request, queryset):
        """Отправить повторно письмо с подтверждением"""
        for user in queryset:
            if not user.email_confirmed:
                try:
                    user.send_confirmation_email(request)
                    self.message_user(request, f'Письмо отправлено на {user.email}.', messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f'Ошибка при отправке на {user.email}: {str(e)}', messages.ERROR)
    resend_confirmation_email.short_description = "Отправить подтверждение email"
    
    def get_queryset(self, request):
        """Ограничение отображения пользователей"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(role='buyer')