from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from products.models import Product

User = get_user_model()

# Полный список статусов согласно ТЗ и требованиям интернет-магазина
ORDER_STATUS_CHOICES = [
    ('pending', 'Ожидает оплаты'),           # Создан, но не оплачен
    ('paid', 'Оплачен'),                     # Оплачен, но еще не подтвержден мастером
    ('processing', 'В обработке'),           # Оплачен и подтвержден мастером
    ('in_work', 'В РАБОТЕ'),                 # Начато изготовление
    ('preparing_for_shipment', 'ГОТОВИТСЯ К ОТПРАВКЕ'),  # Изделие готово, упаковывается
    ('shipped', 'Отправлен'),                # Передан в службу доставки
    ('delivered', 'Доставлен'),              # Получен покупателем
    ('cancelled', 'Отменен'),                # Отменен
]

# Конечные состояния (завершенные заказы)
FINAL_STATUSES = ['delivered', 'cancelled']

# Статусы, после которых нельзя отменить заказ
IRREVERSIBLE_STATUSES = ['in_work', 'preparing_for_shipment', 'shipped', 'delivered']

# Порядок статусов для таймлайна
STATUS_FLOW = [
    'pending',      # 1. Ожидает оплаты
    'paid',         # 2. Оплачен
    'processing',   # 3. В обработке (подтвержден мастером)
    'in_work',      # 4. В РАБОТЕ
    'preparing_for_shipment',  # 5. ГОТОВИТСЯ К ОТПРАВКЕ
    'shipped',      # 6. Отправлен
    'delivered',    # 7. Доставлен
]

# Матрица допустимых переходов статусов (ДКА - детерминированный конечный автомат)
STATUS_TRANSITIONS = {
    'pending': ['paid', 'cancelled'],                    # Можно оплатить или отменить
    'paid': ['processing', 'cancelled'],                 # Мастер подтверждает или отменяет
    'processing': ['in_work', 'cancelled'],              # Начинаем работу или отменяем
    'in_work': ['preparing_for_shipment', 'cancelled'],  # Готовим к отправке или отменяем
    'preparing_for_shipment': ['shipped', 'cancelled'],  # Отправляем или отменяем
    'shipped': ['delivered'],                            # Только доставка
    'delivered': [],                                     # Конечное состояние
    'cancelled': [],                                     # Конечное состояние
}

# Описания этапов для покупателя
STATUS_DESCRIPTIONS = {
    'pending': 'Заказ создан, ожидает оплаты',
    'paid': 'Заказ оплачен, ожидает подтверждения мастера',
    'processing': 'Мастер подтвердил заказ, готовится к работе',
    'in_work': 'Мастер начал изготовление вашего изделия',
    'preparing_for_shipment': 'Изделие готово, упаковывается для отправки',
    'shipped': 'Заказ передан в службу доставки',
    'delivered': 'Заказ доставлен и получен',
    'cancelled': 'Заказ отменен',
}

# Цвета для отображения статусов (CSS классы)
STATUS_COLORS = {
    'pending': 'secondary',
    'paid': 'info',
    'processing': 'primary',
    'in_work': 'warning',
    'preparing_for_shipment': 'warning',
    'shipped': 'success',
    'delivered': 'success',
    'cancelled': 'danger',
}

# Иконки для статусов
STATUS_ICONS = {
    'pending': 'bi-clock',
    'paid': 'bi-credit-card',
    'processing': 'bi-gear',
    'in_work': 'bi-hammer',
    'preparing_for_shipment': 'bi-box-seam',
    'shipped': 'bi-truck',
    'delivered': 'bi-check-circle',
    'cancelled': 'bi-x-circle',
}


class Order(models.Model):
    """Модель заказа с полным циклом статусов hand-made производства"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders',
        null=True,
        blank=True
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Общая сумма'
    )
    status = models.CharField(
        max_length=50, 
        choices=ORDER_STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус заказа'
    )
    
    # Данные для доставки
    delivery_address = models.TextField(verbose_name='Адрес доставки')
    customer_name = models.CharField(
        max_length=255,
        verbose_name='Имя получателя'
    )
    customer_phone = models.CharField(
        max_length=20,
        verbose_name='Телефон'
    )
    customer_email = models.EmailField(verbose_name='Email')
    
    # Дополнительные поля адреса
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Почтовый индекс'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Город'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Область/Регион'
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Страна'
    )
    
    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    # Поля для отслеживания
    tracking_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Трек-номер'
    )
    estimated_delivery_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='Предполагаемая дата доставки'
    )
    
    # Системные поля
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID платежа'
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Способ оплаты'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        permissions = [
            ('can_change_order_status', 'Может изменять статус заказа'),
            ('can_view_all_orders', 'Может просматривать все заказы'),
            ('can_cancel_order', 'Может отменять заказы'),
        ]
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.get_status_display()}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('orders:order_detail', kwargs={'pk': self.id})
    
    def can_change_status(self, new_status, user=None):
        """Проверяет, возможен ли переход в новый статус"""
        # Проверяем, является ли статус конечным
        if self.status in FINAL_STATUSES:
            return False, "Заказ уже завершен"
        
        # Проверяем права пользователя
        if user and not self._has_permission_to_change_status(user):
            return False, "Недостаточно прав для изменения статуса"
        
        # Проверяем допустимость перехода
        allowed_transitions = STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in allowed_transitions:
            current = self.get_status_display()
            new = dict(ORDER_STATUS_CHOICES)[new_status]
            return False, f"Недопустимый переход: {current} → {new}"
        
        # Дополнительные проверки для конкретных статусов
        if new_status == 'cancelled' and self.status in IRREVERSIBLE_STATUSES:
            return False, "Нельзя отменить заказ на этом этапе"
        
        return True, ""
    
    def _has_permission_to_change_status(self, user):
        """Проверяет права пользователя на изменение статуса"""
        # Администраторы могут всё
        if user.is_staff:
            return True
        
        # Мастера могут менять статусы своих заказов
        if user.is_master and self._is_master_order(user):
            return True
        
        # Покупатели могут отменять только свои заказы в статусе pending или paid
        if user == self.user:
            return self.status in ['pending', 'paid']
            
        return False
    
    def _is_master_order(self, user):
        """Проверяет, является ли пользователь мастером для этого заказа"""
        # Проверяем, есть ли товары от этого мастера в заказе
        return self.items.filter(product__master=user).exists()
    
    def update_status(self, new_status, user=None, comment="", photo=None):
        """Изменяет статус заказа с созданием записи в истории"""
        can_change, message = self.can_change_status(new_status, user)
        if not can_change:
            raise ValueError(message)
        
        # Для статуса 'processing' проверяем, что заказ оплачен
        if new_status == 'processing' and self.status != 'paid':
            raise ValueError("Только оплаченные заказы можно переводить в обработку")
        
        # Для статуса 'in_work' проверяем, что заказ подтвержден
        if new_status == 'in_work' and self.status != 'processing':
            raise ValueError("Только подтвержденные заказы можно переводить в работу")
        
        # Создаем запись в истории
        history = OrderStatusHistory.objects.create(
            order=self,
            status=new_status,
            changed_by=user,
            comment=comment[:500] if comment else '',  # Ограничиваем длину
            stage_detail=self._get_stage_detail(new_status),
            photo_report=photo
        )
        
        # Обновляем статус заказа
        old_status = self.status
        self.status = new_status
        self.save()
        
        # Отправляем уведомления
        self._send_notifications(old_status, new_status, comment, user)
        
        # Для кастомных заказов резервируем материалы
        if new_status == 'in_work':
            self._reserve_materials()
        
        # Для отправленных заказов создаем трек-номер если нужно
        if new_status == 'shipped' and not self.tracking_number:
            self.tracking_number = self._generate_tracking_number()
            self.save()
        
        return history
    
    def _get_stage_detail(self, status):
        """Возвращает детализацию этапа на основе статуса"""
        stage_details = {
            'pending': 'Ожидание оплаты от покупателя',
            'paid': 'Заказ оплачен, уведомление отправлено мастеру',
            'processing': 'Мастер подтвердил заказ и готов приступить к работе',
            'in_work': 'Начато изготовление изделия согласно заказу',
            'preparing_for_shipment': 'Изделие готово, проводится контроль качества и упаковка',
            'shipped': 'Заказ передан в службу доставки, трек-номер сгенерирован',
            'delivered': 'Заказ успешно доставлен получателю',
            'cancelled': 'Заказ отменен',
        }
        return stage_details.get(status, '')
    
    def _send_notifications(self, old_status, new_status, comment, user):
        """Отправляет уведомления о смене статуса"""
        # Создаем уведомление в системе для покупателя
        if self.user:
            from notifications.models import Notification
            
            title = f"Статус заказа #{self.id} изменен"
            message = self._format_notification_message(old_status, new_status, comment)
            
            Notification.objects.create(
                user=self.user,
                title=title,
                message=message,
                notification_type='order_status',
                related_object_id=self.id,
                related_object_type='order'
            )
        
        # Отправляем email уведомление (заглушка)
        self._send_status_email(old_status, new_status, comment, user)
    
    def _format_notification_message(self, old_status, new_status, comment):
        """Форматирует сообщение для уведомления"""
        old_display = dict(ORDER_STATUS_CHOICES)[old_status]
        new_display = dict(ORDER_STATUS_CHOICES)[new_status]
        
        message = f"Статус вашего заказа изменен: {old_display} → {new_display}"
        
        if comment:
            message += f"\n\nКомментарий мастера: {comment}"
        
        if new_status == 'shipped' and self.tracking_number:
            message += f"\n\nТрек-номер для отслеживания: {self.tracking_number}"
        
        return message
    
    def _send_status_email(self, old_status, new_status, comment, user):
        """Заглушка для отправки email"""
        pass  # Можно добавить реальную отправку через Celery
    
    def _reserve_materials(self):
        """Резервирует материалы для заказа"""
        try:
            from materials.utils import reserve_materials_for_order
            reserve_materials_for_order(self)
        except ImportError:
            pass  # Если модуль материалов не установлен
    
    def _generate_tracking_number(self):
        """Генерирует трек-номер для заказа"""
        import uuid
        return f"RU{self.id:06d}{uuid.uuid4().hex[:6].upper()}"
    
    def get_status_timeline(self):
        """Возвращает полную хронологию статусов заказа"""
        return self.status_history.all().order_by('changed_at')
    
    def is_final_status(self):
        """Проверяет, является ли текущий статус конечным"""
        return self.status in FINAL_STATUSES
    
    def can_be_cancelled_by_user(self):
        """Может ли пользователь отменить заказ"""
        return self.status in ['pending', 'paid']
    
    def get_status_progress(self):
        """Возвращает прогресс выполнения заказа в процентах"""
        try:
            index = STATUS_FLOW.index(self.status)
            return int((index + 1) / len(STATUS_FLOW) * 100)
        except ValueError:
            return 0 if self.status != 'cancelled' else 100
    
    def get_next_possible_statuses(self, user=None):
        """Возвращает список возможных следующих статусов"""
        if self.is_final_status():
            return []
        
        possible = STATUS_TRANSITIONS.get(self.status, [])
        
        # Фильтруем по правам пользователя
        if user:
            return [s for s in possible if self._can_user_set_status(user, s)]
        
        return possible
    
    def _can_user_set_status(self, user, status):
        """Может ли пользователь установить конкретный статус"""
        if user.is_staff:
            return True
        
        if user.is_master and self._is_master_order(user):
            # Мастера не могут отменять заказы после начала работы
            if status == 'cancelled' and self.status in IRREVERSIBLE_STATUSES:
                return False
            return True
        
        # Покупатели могут только отменять свои заказы
        if user == self.user and status == 'cancelled':
            return self.can_be_cancelled_by_user()
        
        return False
    
    @property
    def status_color(self):
        """Возвращает цвет статуса"""
        return STATUS_COLORS.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Возвращает иконку статуса"""
        return STATUS_ICONS.get(self.status, 'bi-question-circle')
    
    @property
    def status_description(self):
        """Возвращает описание статуса для покупателя"""
        return STATUS_DESCRIPTIONS.get(self.status, '')
    
    def get_timeline_events(self):
        """Возвращает все события заказа в формате для таймлайна"""
        events = []
        
        # Добавляем создание заказа
        events.append({
            'type': 'created',
            'title': 'Заказ создан',
            'description': f'Заказ #{self.id} создан в системе',
            'date': self.created_at,
            'icon': 'bi-cart-plus',
            'color': 'primary'
        })
        
        # Добавляем все изменения статусов
        for history in self.status_history.all().order_by('changed_at'):
            events.append({
                'type': 'status_change',
                'title': f'Статус изменен: {history.get_status_display()}',
                'description': history.comment or history.stage_detail,
                'date': history.changed_at,
                'icon': history.status_icon,
                'color': history.status_color,
                'photo': history.photo_report.url if history.photo_report else None,
                'changed_by': history.changed_by
            })
        
        # Сортируем по дате
        events.sort(key=lambda x: x['date'])
        return events


class OrderItem(models.Model):
    """Элемент заказа - товар в заказе"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Товар'
    )
    quantity = models.IntegerField(
        verbose_name='Количество'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу'
    )
    product_name = models.CharField(
        max_length=200,
        verbose_name='Название товара'
    )

    # Поля для кастомных заказов
    custom_configuration = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Конфигурация кастомного заказа'
    )
    custom_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Цена кастомного заказа'
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
        unique_together = ['order', 'product']  # Один товар может быть только один раз в заказе

    def __str__(self):
        return f"{self.product_name} x{self.quantity} в заказе #{self.order.id}"

    def get_total_price(self):
        """Возвращает общую стоимость позиции"""
        if self.custom_price is not None:
            return self.custom_price * self.quantity
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Автоматически заполняем product_name если не указано
        if not self.product_name and self.product:
            self.product_name = self.product.name
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Модель для хранения истории изменения статусов заказа"""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='status_history'
    )
    status = models.CharField(
        max_length=50, 
        choices=ORDER_STATUS_CHOICES
    )
    stage_detail = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Детализация этапа'
    )
    comment = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Комментарий для покупателя'
    )
    changed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Кто изменил'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата изменения'
    )
    
    # Поля для фотоотчёта
    photo_report = models.ImageField(
        upload_to='order_status_photos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Фотоотчёт'
    )
    
    # Уведомления
    notification_sent = models.BooleanField(
        default=False,
        verbose_name='Уведомление отправлено'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('push', 'Push-уведомление'),
            ('both', 'Оба способа'),
            ('none', 'Не отправлять')
        ],
        default='email',
        verbose_name='Тип уведомления'
    )
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'История статуса заказа'
        verbose_name_plural = 'История статусов заказов'
        indexes = [
            models.Index(fields=['order', 'changed_at']),
            models.Index(fields=['status', 'changed_at']),
        ]
    
    def __str__(self):
        return f"{self.order} → {self.get_status_display()} ({self.changed_at})"
    
    def save(self, *args, **kwargs):
        if not self.stage_detail:
            self.stage_detail = self._get_default_stage_detail()
        
        # Ограничиваем длину комментария
        if self.comment and len(self.comment) > 500:
            self.comment = self.comment[:500]
        
        super().save(*args, **kwargs)
    
    def _get_default_stage_detail(self):
        """Возвращает стандартное описание этапа"""
        return STATUS_DESCRIPTIONS.get(self.status, '')
    
    @property
    def status_color(self):
        """Возвращает цвет статуса"""
        return STATUS_COLORS.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Возвращает иконку статуса"""
        return STATUS_ICONS.get(self.status, 'bi-question-circle')
    