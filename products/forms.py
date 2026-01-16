from django import forms
from .models import Product, Category, ProductImage
from materials.models import Material

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class ProductForm(forms.ModelForm):
    materials = forms.ModelMultipleChoiceField(
        queryset=Material.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label='Материалы'
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'category', 'materials',
            'stock_quantity', 'status', 'technique', 'difficulty_level',
            'production_time_days', 'weight', 'dimensions', 'color',
            'can_be_customized', 'base_cost'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название товара'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание товара'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'technique': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Техника изготовления'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'production_time_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Размеры (например: 10x10x5 см)'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Цвет'}),
            'can_be_customized': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'base_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.master = kwargs.pop('master', None)
        super().__init__(*args, **kwargs)
        # Filter materials to only show master's materials
        if self.master:
            self.fields['materials'].queryset = Material.objects.filter(master=self.master)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.master:
            instance.master = self.master
        if commit:
            instance.save()
            self.save_m2m()
        return instance
