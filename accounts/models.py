from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.mail import send_mail
from django.conf import settings

class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User без username"""
    
    use_in_migrations = True
    
    def _create_user(self, email, password, **extra_fields):
        """Создание и сохранение пользователя с email и паролем"""
        if not email:
            raise ValueError('Email обязателен для заполнения')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('buyer', 'Покупатель'),
        ('master', 'Мастер'),
        ('admin', 'Администратор'),
    ]
    
    username = None  # Убираем стандартное поле username
    email = models.EmailField('Email адрес', unique=True)
    role = models.CharField('Роль', max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)
    email_confirmed = models.BooleanField('Email подтвержден', default=False)
    
    # Адрес для доставки (по умолчанию)
    default_address = models.TextField('Адрес по умолчанию', blank=True)
    default_city = models.CharField('Город', max_length=100, blank=True)
    default_postal_code = models.CharField('Почтовый индекс', max_length=20, blank=True)
    
    # Для мастеров
    master_bio = models.TextField('Описание мастера', blank=True)
    master_specialization = models.CharField('Специализация', max_length=200, blank=True)
    master_experience_years = models.IntegerField('Опыт работы (лет)', default=0)
    master_rating = models.DecimalField('Рейтинг', max_digits=3, decimal_places=2, default=0)
    
    # Предпочтения
    newsletter_subscription = models.BooleanField('Подписка на рассылку', default=True)
    
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    # Используем кастомный менеджер
    objects = UserManager()
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.email
    
    def is_master(self):
        return self.role == 'master'
    
    def is_buyer(self):
        return self.role == 'buyer'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_full_address(self):
        """Получить полный адрес"""
        parts = []
        if self.default_address:
            parts.append(self.default_address)
        if self.default_city:
            parts.append(self.default_city)
        if self.default_postal_code:
            parts.append(self.default_postal_code)
        return ', '.join(parts)
    
    def send_confirmation_email(self, request):
        """Упрощенная отправка письма с подтверждением email"""
        from .tokens import email_confirmation_token
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = email_confirmation_token.make_token(self)
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        
        confirmation_link = f"http://127.0.0.1:8000/accounts/confirm-email/{uid}/{token}/"
        
        subject = 'Подтверждение email для магазина рукодельных изделий'
        message = f"""
        Здравствуйте, {self.first_name or self.email}!
        
        Благодарим за регистрацию в нашем магазине рукодельных изделий.
        
        Для подтверждения вашего email и активации аккаунта, пожалуйста, перейдите по ссылке:
        {confirmation_link}
        
        Если вы не регистрировались в нашем магазине, проигнорируйте это письмо.
        
        С уважением,
        Команда Мастерской
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )
        
        print("\n" + "="*60)
        print("ВАЖНО: Ссылка для подтверждения email (скопируйте и откройте в браузере):")
        print(confirmation_link)
        print("="*60 + "\n")