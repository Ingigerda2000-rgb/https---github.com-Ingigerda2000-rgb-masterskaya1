from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderStatusHistory, STATUS_TRANSITIONS, ORDER_STATUS_CHOICES


class OrderStatusUpdateForm(forms.ModelForm):
    """Форма для изменения статуса заказа мастером/администратором"""
    comment = forms.CharField(
        label='Комментарий для покупателя',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Опишите текущий этап работы (до 500 символов)...',
            'maxlength': 500,
            'class': 'form-control'
        }),
        required=False,
        help_text='Будет отправлен покупателю в уведомлении'
    )
    photo_report = forms.ImageField(
        label='Фотоотчёт',
        required=False,
        help_text='JPG/PNG, не более 10 МБ. Покажет прогресс работы покупателю',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png'
        })
    )
    send_notification = forms.BooleanField(
        label='Отправить уведомление покупателю',
        initial=True,
        required=False,
        help_text='Отправить email или push-уведомление о смене статуса'
    )
    
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.order and self.user:
            # Получаем возможные следующие статусы
            possible_statuses = self.order.get_next_possible_statuses(self.user)
            
            # Фильтруем choices поля status
            self.fields['status'].choices = [
                (code, label) for code, label in ORDER_STATUS_CHOICES 
                if code in possible_statuses
            ]
            
            # Если возможен только один статус, делаем его выбранным по умолчанию
            if len(possible_statuses) == 1:
                self.fields['status'].initial = possible_statuses[0]
    
    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get('status')
        
        if self.order and self.user and new_status:
            can_change, message = self.order.can_change_status(new_status, self.user)
            if not can_change:
                raise ValidationError(message)
            
            # Проверяем размер файла
            photo = cleaned_data.get('photo_report')
            if photo and photo.size > 10 * 1024 * 1024:  # 10 MB
                raise ValidationError({
                    'photo_report': 'Файл слишком большой. Максимальный размер - 10 МБ.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.order and self.user:
            comment = self.cleaned_data.get('comment', '')
            photo = self.cleaned_data.get('photo_report')
            send_notification = self.cleaned_data.get('send_notification', True)
            
            try:
                # Используем метод update_status для создания записи в истории
                history = self.order.update_status(
                    new_status=self.cleaned_data['status'],
                    user=self.user,
                    comment=comment,
                    photo=photo
                )
                
                # Настраиваем отправку уведомлений
                history.notification_sent = send_notification
                if not send_notification:
                    history.notification_type = 'none'
                history.save()
                
            except ValueError as e:
                raise ValidationError(str(e))
        
        return instance


class CustomerCancelOrderForm(forms.Form):
    """Форма для отмены заказа покупателем"""
    reason = forms.ChoiceField(
        label='Причина отмены',
        choices=[
            ('changed_mind', 'Передумал(а) покупать'),
            ('found_cheaper', 'Нашел(а) дешевле'),
            ('delivery_issues', 'Проблемы с доставкой'),
            ('quality_concerns', 'Сомнения в качестве'),
            ('other', 'Другая причина')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    comment = forms.CharField(
        label='Комментарий (необязательно)',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Уточните причину отмены...',
            'class': 'form-control'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.order and not self.order.can_be_cancelled_by_user():
            raise ValidationError("Этот заказ нельзя отменить")
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.order and self.user:
            if self.user != self.order.user:
                raise ValidationError("Вы можете отменять только свои заказы")
            
            if not self.order.can_be_cancelled_by_user():
                raise ValidationError("Этот заказ нельзя отменить")
        
        return cleaned_data
    
    def save(self):
        """Отменяет заказ"""
        if self.order and self.user:
            comment = f"Отменено покупателем. Причина: {self.get_reason_display()}"
            if self.cleaned_data.get('comment'):
                comment += f". Комментарий: {self.cleaned_data['comment']}"
            
            return self.order.update_status(
                new_status='cancelled',
                user=self.user,
                comment=comment
            )
    
    def get_reason_display(self):
        """Возвращает читаемое описание причины"""
        reasons = {
            'changed_mind': 'Передумал(а) покупать',
            'found_cheaper': 'Нашел(а) дешевле',
            'delivery_issues': 'Проблемы с доставкой',
            'quality_concerns': 'Сомнения в качестве',
            'other': 'Другая причина'
        }
        return reasons.get(self.cleaned_data.get('reason', ''), '')


class StatusFilterForm(forms.Form):
    """Форма фильтрации заказов по статусу"""
    status = forms.ChoiceField(
        choices=[('', 'Все статусы')] + ORDER_STATUS_CHOICES,
        required=False,
        label='Статус заказа',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        label='С даты',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        label='По дату',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ID, имя, email, телефон...'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Дата "С" не может быть больше даты "По"')
        
        return cleaned_data