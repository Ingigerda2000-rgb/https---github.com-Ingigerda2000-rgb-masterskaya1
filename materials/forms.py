from django import forms
from django.core.validators import MinValueValidator
from .models import Material, MaterialRecipe

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = [
            'name', 'current_quantity', 'unit', 'min_quantity',
            'price_per_unit', 'color', 'texture', 'supplier',
            'supplier_contact', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Шерсть мериноса, Хлопковая ткань...'
            }),
            'current_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'min_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: красный, синий, бежевый'
            }),
            'texture': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: гладкая, шероховатая, ворсистая'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название поставщика'
            }),
            'supplier_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Телефон, email или сайт поставщика'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительная информация о материале...'
            }),
            'unit': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'current_quantity': 'Текущее количество на складе',
            'min_quantity': 'Минимальный остаток (когда заказывать новый)',
            'price_per_unit': 'Цена за единицу (руб.)',
        }
    
    def __init__(self, *args, **kwargs):
        self.master = kwargs.pop('master', None)
        super().__init__(*args, **kwargs)
        
        # Добавляем валидаторы
        self.fields['current_quantity'].validators.append(MinValueValidator(0))
        self.fields['min_quantity'].validators.append(MinValueValidator(0))
        self.fields['price_per_unit'].validators.append(MinValueValidator(0))
    
    def clean(self):
        cleaned_data = super().clean()
        min_qty = cleaned_data.get('min_quantity')
        current_qty = cleaned_data.get('current_quantity')
        
        if min_qty is not None and current_qty is not None:
            if min_qty > current_qty:
                self.add_error(
                    'min_quantity',
                    'Минимальный запас не может превышать текущее количество'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.master:
            instance.master = self.master
        if commit:
            instance.save()
        return instance


class MaterialRecipeForm(forms.ModelForm):
    class Meta:
        model = MaterialRecipe
        fields = ['material', 'consumption_rate', 'waste_factor', 'auto_consume']
        widgets = {
            'material': forms.Select(attrs={'class': 'form-select'}),
            'consumption_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'waste_factor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1'
            }),
            'auto_consume': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'consumption_rate': 'Норма расхода на 1 единицу изделия',
            'waste_factor': 'Коэффициент отходов (0.1 = 10%)',
            'auto_consume': 'Автоматически списывать при производстве',
        }
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

        # Фильтруем материалы только текущего мастера
        if self.product and self.product.master:
            self.fields['material'].queryset = Material.objects.filter(
                master=self.product.master,
                is_active=True
            ).order_by('name')

        # Добавляем класс для JS
        self.fields['material'].widget.attrs['class'] = 'form-select material-select'
        
        # Добавляем валидаторы
        self.fields['consumption_rate'].validators.append(MinValueValidator(0.001))
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.product:
            instance.product = self.product
        if commit:
            instance.save()
        return instance


class QuickMaterialForm(forms.Form):
    """Форма для быстрого добавления материала"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название материала'
        })
    )
    current_quantity = forms.DecimalField(
        max_digits=12,
        decimal_places=3,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'min': '0'
        })
    )
    unit = forms.ChoiceField(
        choices=Material.UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )