from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    """Форма оформления заказа"""
    promo_code = forms.CharField(
        required=False,
        label='Промокод',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите промокод, если есть'
        })
    )
    
    class Meta:
        model = Order
        fields = [
            'customer_name',
            'customer_phone',
            'customer_email',
            'region',
            'city',
            'street',
            'house',
            'apartment',
            'delivery_method',
            'payment_method',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 XXX XXX XX XX'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Московская область'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Москва'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: ул. Ленина'}),
            'house': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 10'}),
            'apartment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: 42'}),
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Заполняем данные пользователя по умолчанию
        if self.user:
            if not self.instance.customer_name and (self.user.first_name or self.user.last_name):
                self.initial['customer_name'] = f"{self.user.first_name} {self.user.last_name}".strip()
            if not self.instance.customer_email:
                self.initial['customer_email'] = self.user.email
            if not self.instance.customer_phone:
                self.initial['customer_phone'] = self.user.phone
            
            # Заполняем адрес из профиля пользователя
            if self.user.default_city:
                self.initial['city'] = self.user.default_city
            if self.user.default_postal_code:
                self.initial['region'] = self.user.default_postal_code
            if self.user.default_address:
                # Пытаемся разделить адрес на улицу и дом
                address_parts = self.user.default_address.split(',')
                if len(address_parts) >= 2:
                    self.initial['street'] = address_parts[0].strip()
                    self.initial['house'] = address_parts[1].strip()
                else:
                    self.initial['street'] = self.user.default_address
    
    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone')
        # Простая валидация телефона
        if phone:
            phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not phone.startswith('+7') and not phone.startswith('8'):
                phone = '+7' + phone[-10:]
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Формируем полный адрес доставки из отдельных полей
        region = cleaned_data.get('region', '')
        city = cleaned_data.get('city', '')
        street = cleaned_data.get('street', '')
        house = cleaned_data.get('house', '')
        apartment = cleaned_data.get('apartment', '')
        
        address_parts = []
        if region:
            address_parts.append(f"Регион: {region}")
        if city:
            address_parts.append(f"Город: {city}")
        if street:
            address_parts.append(f"Улица: {street}")
        if house:
            address_parts.append(f"Дом: {house}")
        if apartment:
            address_parts.append(f"Квартира: {apartment}")
        
        full_address = ", ".join(address_parts)
        cleaned_data['delivery_address'] = full_address
        
        return cleaned_data
