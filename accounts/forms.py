from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите email',
            'autocomplete': 'email'
        })
    )

    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите пароль',
            'autocomplete': 'new-password'
        }),
        help_text="Пароль должен содержать минимум 8 символов, буквы и цифры"
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Повторите пароль',
            'autocomplete': 'new-password'
        })
    )
    role = forms.ChoiceField(
        label='Роль',
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='Имя',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите имя'
        })
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите фамилию'
        })
    )
    phone = forms.CharField(
        label='Телефон',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+7 (999) 123-45-67'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'role', 
                 'first_name', 'last_name', 'phone')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Можно добавить валидацию телефона
        return phone

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите email',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password'
        })
    )
    
    error_messages = {
        'invalid_login': "Неверный email или пароль.",
        'inactive': "Этот аккаунт неактивен.",
    }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar', 
                 'default_address', 'default_city', 'default_postal_code']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'default_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'default_city': forms.TextInput(attrs={'class': 'form-control'}),
            'default_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле аватара необязательным
        self.fields['avatar'].required = False
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Валидация телефона (можно расширить)
        if phone and not phone.startswith('+'):
            raise ValidationError('Телефон должен начинаться с +')
        return phone

class MasterProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar',
                 'master_bio', 'master_specialization', 
                 'master_experience_years']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'master_bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'master_specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'master_experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
        }