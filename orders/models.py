from django.db import models
from django.utils import timezone
from django.db import transaction
from accounts.models import User
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    DELIVERY_METHODS = [
        ('courier', 'Курьерская доставка'),
        ('post', 'Почта России'),
        ('pickup', 'Самовывоз'),
        ('sdek', 'СДЭК'),
        ('boxberry', 'Boxberry'),
    ]
    
    PAYMENT_METHODS = [
        ('card_online', 'Картой онлайн'),
        ('sbp', 'СБП (Система быстрых платежей)'),
        ('cash_on_delivery', 'Наложенный платеж'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    order_number = models.CharField('Номер заказа', max_length=20, unique=True)
    total_amount = models.DecimalField('Общая сумма', max_digits=10, decimal_places=2)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Данные доставки
    region = models.CharField('Регион', max_length=100, blank=True)
    city = models.CharField('Город', max_length=100, blank=True)
    street = models.CharField('Улица', max_length=200, blank=True)
    house = models.CharField('Дом', max_length=20, blank=True)
    apartment = models.CharField('Квартира', max_length=20, blank=True)
    delivery_address = models.TextField('Полный адрес доставки')
    customer_name = models.CharField('Имя получателя', max_length=100)
    customer_phone = models.CharField('Телефон', max_length=20)
    customer_email = models.EmailField('Email')
    
    # Доставка
    delivery_cost = models.DecimalField('Стоимость доставки', max_digits=10, decimal_places=2, default=0)
    delivery_method = models.CharField('Способ доставки', max_length=50, choices=DELIVERY_METHODS, blank=True)
    tracking_number = models.CharField('Трек-номер', max_length=100, blank=True)
    
    # Оплата
    payment_method = models.CharField('Способ оплаты', max_length=50, choices=PAYMENT_METHODS, blank=True)
    payment_id = models.CharField('ID платежа', max_length=100, blank=True)
    paid_at = models.DateTimeField('Дата оплаты', null=True, blank=True)
    
    # Скидки
    discount_amount = models.DecimalField('Сумма скидки', max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField('Промокод', max_length=50, blank=True)
    
    # Комментарий к заказу
    customer_notes = models.TextField('Комментарий покупателя', blank=True)
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Заказ #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Генерация номера заказа: ГОДМЕС-ПОСЛЕДОВАТЕЛЬНЫЙ НОМЕР
            year_month = timezone.now().strftime('%Y%m')
            last_order = Order.objects.filter(
                order_number__startswith=year_month
            ).order_by('-order_number').first()
            
            if last_order:
                try:
                    last_num = int(last_order.order_number.split('-')[1])
                    new_num = last_num + 1
                except (IndexError, ValueError):
                    new_num = 1
            else:
                new_num = 1
            
            self.order_number = f"{year_month}-{new_num:04d}"
        
        # При сохранении пересчитываем сумму
        if not self.total_amount:
            self.total_amount = self.calculate_total_amount()
        
        super().save(*args, **kwargs)
    
    # ============ МАТЕМАТИЧЕСКИЕ РАСЧЁТЫ ============
    
    def calculate_items_total(self):
        """Расчёт суммы товаров в заказе"""
        items_total = sum(item.calculate_subtotal() for item in self.items.all())
        return items_total
    
    def calculate_total_amount(self):
        """Расчёт общей суммы заказа с учётом доставки и скидки"""
        items_total = self.calculate_items_total()
        total = items_total + self.delivery_cost - self.discount_amount
        
        # Гарантируем, что сумма не будет отрицательной
        return max(total, 0)
    
    def calculate_discount(self, promo_code_str=None):
        """
        Расчёт скидки по промокоду согласно математической постановке из ТЗ:
        C = {
            0.1 × T_base, если T_base ≥ 5000 ∧ promo = 'SUMMER10'
            0.05 × T_base, если T_base ≥ 3000
            0, иначе
        }
        """
        items_total = self.calculate_items_total()
        
        if promo_code_str and promo_code_str.upper() == 'SUMMER10' and items_total >= 5000:
            # Скидка 10% для промокода SUMMER10 при заказе от 5000
            return items_total * 0.1
        
        elif items_total >= 5000:
            # Скидка 10% для заказов от 5000
            return items_total * 0.1
        
        elif items_total >= 3000:
            # Скидка 5% для заказов от 3000
            return items_total * 0.05
        
        else:
            return 0
    
    def calculate_delivery_cost(self, address=None):
        """
        Расчёт стоимости доставки
        В реальной системе здесь была бы интеграция с API служб доставки
        """
        items_total = self.calculate_items_total()
        
        # Бесплатная доставка от 5000 руб
        if items_total >= 5000:
            return 0
        
        # Базовая стоимость доставки
        base_cost = 300
        
        # Учитываем метод доставки
        if self.delivery_method == 'courier':
            return base_cost + 100  # +100 за курьерскую доставку
        elif self.delivery_method == 'sdek' or self.delivery_method == 'boxberry':
            return base_cost + 150  # +150 за СДЭК/Boxberry
        elif self.delivery_method == 'post':
            return base_cost + 50   # +50 за Почту России
        elif self.delivery_method == 'pickup':
            return 0  # Самовывоз бесплатно
        else:
            return base_cost
    
    # ============ МЕТОДЫ ДЛЯ РАБОТЫ С ЗАКАЗОМ ============
    
    @classmethod
    def create_from_cart(cls, cart, delivery_data, promo_code=None):
        """
        Создание заказа из корзины
        cart - объект корзины
        delivery_data - словарь с данными доставки
        promo_code - промокод (опционально)
        """
        with transaction.atomic():
            # Создаем заказ
            order = cls(
                user=cart.user,
                customer_name=delivery_data.get('customer_name', cart.user.get_full_name()),
                customer_phone=delivery_data.get('customer_phone', cart.user.phone),
                customer_email=delivery_data.get('customer_email', cart.user.email),
                delivery_address=delivery_data.get('delivery_address', ''),
                delivery_method=delivery_data.get('delivery_method', 'courier'),
                payment_method=delivery_data.get('payment_method', 'card_online'),
                customer_notes=delivery_data.get('customer_notes', ''),
                promo_code=promo_code or '',
            )
            
            # Сохраняем, чтобы получить order_number
            order.save()
            
            # Рассчитываем стоимость доставки
            order.delivery_cost = order.calculate_delivery_cost()
            
            # Рассчитываем скидку
            order.discount_amount = order.calculate_discount(promo_code)
            
            # Рассчитываем итоговую сумму
            order.total_amount = order.calculate_total_amount()
            
            # Переносим товары из корзины в заказ
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    product_name=cart_item.product.name
                )
                
                # Обновляем остатки товаров
                product = cart_item.product
                product.stock_quantity -= cart_item.quantity
                product.save()
                
                # Резервируем материалы для товара (если есть рецепты)
                if hasattr(product, 'reserve_materials_for_order'):
                    product.reserve_materials_for_order(cart_item.quantity, order.id)
            
            # Очищаем корзину
            cart.clear()
            
            # Создаем запись в истории статусов
            OrderStatusHistory.objects.create(
                order=order,
                status='accepted',
                stage_detail='Заказ принят в обработку',
                comment='Заказ создан из корзины пользователя',
                changed_by=cart.user if cart.user else None,
                notify_customer=True
            )
            
            order.save()
            return order
    
    def process_payment(self, payment_data):
        """
        Обработка оплаты заказа
        В реальной системе здесь была бы интеграция с платёжным шлюзом
        """
        # В реальной системе здесь:
        # 1. Создание платежа в платёжной системе (ЮKassa и т.д.)
        # 2. Получение ссылки для оплаты
        # 3. Ожидание вебхука о подтверждении платежа
        
        # Для демо просто меняем статус
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.payment_id = payment_data.get('payment_id', f"demo_{self.order_number}")
        self.save()
        
        # Добавляем запись в историю
        OrderStatusHistory.objects.create(
            order=self,
            status='paid',
            stage_detail='Заказ оплачен',
            comment=f'Оплата через {self.get_payment_method_display()}',
            changed_by=self.user,
            notify_customer=True
        )
        
        # Отправляем уведомление покупателю
        self._send_notification('payment_success')
        
        return True
    
    def update_status(self, new_status, comment='', photo=None, changed_by=None):
        """
        Обновление статуса заказа с записью в историю
        """
        valid_transitions = {
            'pending': ['paid', 'cancelled'],
            'paid': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered', 'cancelled'],
            'delivered': [],  # Конечный статус
            'cancelled': [],  # Конечный статус
        }
        
        current_status = self.status
        
        # Проверяем валидность перехода статусов
        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(
                f"Недопустимый переход статуса: {current_status} → {new_status}"
            )
        
        with transaction.atomic():
            # Обновляем статус заказа
            self.status = new_status
            self.save()
            
            # Создаем запись в истории
            OrderStatusHistory.objects.create(
                order=self,
                status=self._map_status_to_history_status(new_status),
                stage_detail=self._get_stage_detail(new_status),
                comment=comment,
                photo=photo,
                changed_by=changed_by,
                notify_customer=True
            )
            
            # Если заказ отменен, возвращаем товары на склад
            if new_status == 'cancelled':
                self._restore_stock()
            
            # Если заказ доставлен, списываем материалы
            elif new_status == 'delivered':
                self._consume_materials()
            
            # Отправляем уведомление
            self._send_notification('status_changed', new_status=new_status)
    
    def _map_status_to_history_status(self, order_status):
        """Маппинг статусов заказа на статусы истории"""
        mapping = {
            'pending': 'accepted',
            'paid': 'agreed',
            'processing': 'in_production',
            'shipped': 'shipped',
            'delivered': 'delivered',
            'cancelled': 'cancelled',
        }
        return mapping.get(order_status, 'accepted')
    
    def _get_stage_detail(self, status):
        """Получение детализации этапа для истории"""
        details = {
            'pending': 'Заказ ожидает оплаты',
            'paid': 'Заказ оплачен и принят в работу',
            'processing': 'Заказ в производстве',
            'shipped': 'Заказ отправлен покупателю',
            'delivered': 'Заказ доставлен получателю',
            'cancelled': 'Заказ отменен',
        }
        return details.get(status, '')
    
    def _restore_stock(self):
        """Возврат товаров на склад при отмене заказа"""
        for item in self.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()
            
            # Освобождаем зарезервированные материалы
            if hasattr(product, 'release_materials_for_order'):
                product.release_materials_for_order(item.quantity, self.id)
    
    def _consume_materials(self):
        """Списание материалов при завершении заказа"""
        for item in self.items.all():
            product = item.product
            if hasattr(product, 'check_material_availability'):
                # Проверяем наличие материалов
                unavailable = product.check_material_availability(item.quantity)
                if not unavailable:
                    # Списываем материалы
                    if hasattr(product, 'reserve_materials_for_order'):
                        # В реальной системе здесь было бы списание
                        pass
    
    def _send_notification(self, notification_type, **kwargs):
        """
        Отправка уведомления покупателю
        В реальной системе здесь была бы отправка email/SMS
        """
        # TODO: Реализовать отправку уведомлений через celery
        print(f"Уведомление для заказа #{self.order_number}: {notification_type}")
    
    def get_status_history(self):
        """Получение истории статусов заказа"""
        return self.status_history.all().order_by('changed_at')
    
    def can_be_cancelled(self):
        """Проверка, можно ли отменить заказ"""
        return self.status in ['pending', 'paid', 'processing']
    
    def get_items_count(self):
        """Получение количества товаров в заказе"""
        return self.items.count()
    
    # ============ МЕТОДЫ ДЛЯ ОТЧЁТНОСТИ ============
    
    def generate_invoice(self):
        """Генерация счёта на оплату (заглушка)"""
        # В реальной системе здесь генерировался бы PDF счёта
        return {
            'order_number': self.order_number,
            'date': self.created_at.strftime('%d.%m.%Y'),
            'customer': self.customer_name,
            'items': [
                {
                    'name': item.product_name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': float(item.calculate_subtotal())
                }
                for item in self.items.all()
            ],
            'delivery': float(self.delivery_cost),
            'discount': float(self.discount_amount),
            'total': float(self.total_amount),
        }
    
    # ============ СВОЙСТВА ============
    
    @property
    def items_total(self):
        """Сумма товаров (property)"""
        return self.calculate_items_total()
    
    @property
    def final_total(self):
        """Итоговая сумма с учётом всех начислений (property)"""
        return self.calculate_total_amount()
    
    @property
    def has_discount(self):
        """Есть ли скидка на заказ"""
        return self.discount_amount > 0
    
    @property
    def delivery_method_display(self):
        """Отображаемое название способа доставки"""
        return dict(self.DELIVERY_METHODS).get(self.delivery_method, self.delivery_method)
    
    @property
    def payment_method_display(self):
        """Отображаемое название способа оплаты"""
        return dict(self.PAYMENT_METHODS).get(self.payment_method, self.payment_method)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.IntegerField('Количество')
    price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)
    product_name = models.CharField('Название товара', max_length=200)
    
    # Для кастомных заказов
    custom_configuration = models.JSONField('Конфигурация кастомного заказа', null=True, blank=True)
    custom_price = models.DecimalField('Цена кастомного заказа', max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def calculate_subtotal(self):
        """Расчёт стоимости позиции"""
        if self.custom_price:
            return self.custom_price * self.quantity
        return self.price * self.quantity
    
    def get_final_price(self):
        """Получение итоговой цены за единицу"""
        return self.custom_price if self.custom_price else self.price
    
    @property
    def is_custom(self):
        """Является ли товар кастомным заказом"""
        return bool(self.custom_configuration)

class OrderStatusHistory(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'ПРИНЯТ'),
        ('agreed', 'СОГЛАСОВАН'),
        ('in_production', 'В РАБОТЕ'),
        ('preparing_for_shipment', 'ГОТОВИТСЯ К ОТПРАВКЕ'),
        ('shipped', 'ОТПРАВЛЕН'),
        ('delivered', 'ДОСТАВЛЕН'),
        ('cancelled', 'ОТМЕНЁН'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField('Статус', max_length=50, choices=STATUS_CHOICES)
    stage_detail = models.TextField('Детализация этапа', blank=True)
    comment = models.TextField('Комментарий', blank=True)
    photo = models.ImageField('Фотоотчёт', upload_to='order_status/', blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='changed_orders')
    changed_at = models.DateTimeField('Время изменения', auto_now_add=True)
    notify_customer = models.BooleanField('Уведомить покупателя', default=True)
    
    class Meta:
        verbose_name = 'История статуса заказа'
        verbose_name_plural = 'История статусов заказов'
        ordering = ['changed_at']  # Изменено на прямой порядок для отображения хронологии
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"
    
    def get_status_display_ru(self):
        """Получение отображаемого названия статуса на русском"""
        status_map = {
            'accepted': 'ПРИНЯТ',
            'agreed': 'СОГЛАСОВАН',
            'in_production': 'В РАБОТЕ',
            'preparing_for_shipment': 'ГОТОВИТСЯ К ОТПРАВКЕ',
            'shipped': 'ОТПРАВЛЕН',
            'delivered': 'ДОСТАВЛЕН',
            'cancelled': 'ОТМЕНЁН',
        }
        return status_map.get(self.status, self.status)
    
    @property
    def has_photo(self):
        """Есть ли фотоотчёт"""
        return bool(self.photo)