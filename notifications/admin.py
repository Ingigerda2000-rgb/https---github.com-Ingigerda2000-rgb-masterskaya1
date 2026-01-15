from django.contrib import admin
from django.utils.html import format_html
from .models import Notification
from accounts.models import User

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at', 'read_at')
    list_filter = ('notification_type', 'is_read', 'created_at', 'sent_via_email', 'sent_via_push')
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('created_at', 'read_at', 'mark_as_read_button')
    list_editable = ('is_read',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Связанный объект', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('Статус доставки', {
            'fields': ('is_read', 'mark_as_read_button', 'sent_via_email', 'sent_via_push')
        }),
        ('Даты', {
            'fields': ('created_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mark_as_read_button(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green; font-weight: bold;">✓ Прочитано</span>')
        else:
            return format_html(
                '<a href="{}" class="button">Пометить как прочитанное</a>',
                f'/admin/notifications/notification/{obj.id}/mark_as_read/'
            )
    mark_as_read_button.short_description = 'Действие'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/mark_as_read/', self.mark_as_read, name='mark_as_read'),
        ]
        return custom_urls + urls
    
    def mark_as_read(self, request, object_id):
        from django.shortcuts import redirect
        notification = self.get_object(request, object_id)
        notification.mark_as_read()
        self.message_user(request, f'Уведомление #{notification.id} помечено как прочитанное')
        return redirect('..')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs