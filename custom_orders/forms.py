from django import forms
from .models import CustomOrderSpecification

class CustomOrderForm(forms.ModelForm):
    """Форма для создания кастомного заказа"""
    
    class Meta:
        model = CustomOrderSpecification
        fields = ['customer_notes']
        widgets = {
            'customer_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные пожелания к заказу...'
            }),
        }