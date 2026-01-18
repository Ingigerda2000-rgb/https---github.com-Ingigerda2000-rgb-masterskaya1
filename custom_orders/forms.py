from django import forms
from .models import CustomOrderSpecification

class CustomOrderForm(forms.ModelForm):
    """Форма для создания и редактирования кастомного заказа"""

    class Meta:
        model = CustomOrderSpecification
        fields = ['total_price', 'production_days', 'customer_notes', 'approval_notes']
        widgets = {
            'total_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'production_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'customer_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные пожелания к заказу...'
            }),
            'approval_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Примечания мастера...'
            }),
        }
