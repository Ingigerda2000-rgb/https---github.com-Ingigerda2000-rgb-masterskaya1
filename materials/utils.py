# materials/utils.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from django.db import models
from django.db.models import Sum, F, Avg, Count
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import Material, MaterialReservation, MaterialRecipe

class MaterialManager:
    """Менеджер для работы с материалами"""
    
    @staticmethod
    def get_material_report(master_id):
        """Получить отчёт по материалам для мастера"""
        materials = Material.objects.filter(master_id=master_id, is_active=True)
        
        # Общая стоимость запасов
        total_value_result = materials.aggregate(
            total_value=Sum(F('current_quantity') * F('price_per_unit'))
        )
        total_value = total_value_result['total_value'] or Decimal('0')
        
        # Материалы с низким запасом
        low_stock_materials = materials.filter(
            current_quantity__lte=F('min_quantity'),
            current_quantity__gt=0
        )
        
        # Материалы, которые закончились
        out_of_stock = materials.filter(current_quantity=0)
        
        # Материалы, которые скоро закончатся (менее 125% от минимума)
        warning_stock = materials.filter(
            current_quantity__lte=F('min_quantity') * Decimal('1.25'),
            current_quantity__gt=F('min_quantity')
        )
        
        report = {
            'total_materials': materials.count(),
            'low_stock': low_stock_materials.count(),
            'warning_stock': warning_stock.count(),
            'out_of_stock': out_of_stock.count(),
            'total_value': total_value,
            'materials': []
        }
        
        # Подготовка данных для отображения
        for material in materials:
            # Рассчитываем стоимость запаса
            stock_value = material.stock_value
            
            # Определяем статус
            if material.current_quantity == 0:
                status = 'out_of_stock'
                status_text = 'Нет в наличии'
                status_class = 'danger'
            elif material.current_quantity <= material.min_quantity:
                status = 'low_stock'
                status_text = 'Низкий запас'
                status_class = 'warning'
            elif material.current_quantity <= material.min_quantity * Decimal('1.25'):
                status = 'warning_stock'
                status_text = 'Скоро закончится'
                status_class = 'info'
            else:
                status = 'normal'
                status_text = 'В норме'
                status_class = 'success'
            
            # Рассчитываем, на сколько хватит запаса (если есть расход)
            days_left = None
            if hasattr(material, 'recipes') and material.recipes.exists():
                # Берём средний расход
                avg_result = material.recipes.aggregate(
                    avg=Avg('consumption_rate')
                )
                avg_consumption = avg_result['avg']
                if avg_consumption and avg_consumption > 0:
                    # Предполагаем 1 изделие в день для простоты
                    days_left = int(float(material.current_quantity) / float(avg_consumption))
            
            material_data = {
                'id': material.id,
                'name': material.name,
                'current_quantity': float(material.current_quantity),
                'min_quantity': float(material.min_quantity),
                'unit': material.get_unit_display(),
                'price_per_unit': float(material.price_per_unit),
                'value': float(stock_value),
                'status': status,
                'status_text': status_text,
                'status_class': status_class,
                'days_left': days_left,
                'color': material.color or '—',
                'supplier': material.supplier or '—',
                'notes': material.notes or '',
            }
            report['materials'].append(material_data)
        
        return report
    
    @staticmethod
    def check_and_notify_low_stock():
        """Проверить материалы с низким запасом и отправить уведомления"""
        from accounts.models import User
        
        # Получаем всех мастеров
        masters = User.objects.filter(role='master', is_active=True)
        
        total_notifications = 0
        
        for master in masters:
            low_stock_materials = Material.objects.filter(
                master=master,
                is_active=True,
                current_quantity__lte=F('min_quantity'),
                current_quantity__gt=0
            )
            
            if low_stock_materials.exists():
                try:
                    subject = f"⚠️ Низкий запас материалов в HandMadeShop"
                    
                    # Создаём список материалов с низким запасом
                    materials_list = "\n".join([
                        f"• {mat.name}: {mat.current_quantity} {mat.get_unit_display()} "
                        f"(мин.: {mat.min_quantity} {mat.get_unit_display()})"
                        for mat in low_stock_materials
                    ])
                    
                    message = f"""
Уважаемый(ая) {master.get_full_name() or master.email},

У вас есть материалы с низким запасом, которые требуют пополнения:

{materials_list}

📊 Рекомендуем заказать эти материалы как можно скорее,
чтобы не прерывать производственный процесс.

Для просмотра детальной информации перейдите в раздел "Материалы" → "Низкий запас".

С уважением,
Команда HandMadeShop
"""
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[master.email],
                        fail_silently=True,
                    )
                    
                    total_notifications += 1
                    print(f"Отправлено уведомление мастеру {master.email}")
                    
                except Exception as e:
                    print(f"Ошибка отправки уведомления для {master.email}: {e}")
        
        return total_notifications
    
    @staticmethod
    def get_consumption_report(master_id, start_date, end_date):
        """
        Отчёт по расходу материалов за период
        """
        # Используем __range для фильтрации по дате
        consumptions = MaterialReservation.objects.filter(
            material__master_id=master_id,
            status='consumed',
            consumed_at__range=(start_date, end_date)
        ).select_related('material').values(
            'material__name',
            'material__unit'
        ).annotate(
            total_consumed=Sum('quantity'),
            total_cost=Sum(F('quantity') * F('material__price_per_unit'))
        ).order_by('-total_consumed')
        
        # Форматируем результат
        formatted_consumptions = []
        for cons in consumptions:
            total_consumed = cons['total_consumed'] or Decimal('0')
            total_cost = cons['total_cost'] or Decimal('0')
            
            formatted_consumptions.append({
                'material_name': cons['material__name'],
                'unit': cons['material__unit'],
                'total_consumed': float(total_consumed),
                'total_cost': float(total_cost),
            })
        
        return formatted_consumptions
    
    @staticmethod
    def get_material_usage_by_product(master_id, product_id=None):
        """
        Анализ использования материалов по изделиям
        """
        from products.models import Product
        
        query = MaterialRecipe.objects.filter(
            material__master_id=master_id
        ).select_related('product', 'material')
        
        if product_id:
            query = query.filter(product_id=product_id)
        
        usage_data = []
        for recipe in query:
            material = recipe.material
            
            # Рассчитываем, сколько можно произвести с текущими запасами
            if material.current_quantity > 0 and recipe.consumption_rate > 0:
                try:
                    can_produce = int(float(material.current_quantity) / float(recipe.consumption_rate))
                except:
                    can_produce = 0
            else:
                can_produce = 0
            
            # Рассчитываем стоимость материала на единицу изделия
            material_cost_per_product = recipe.consumption_rate * material.price_per_unit
            
            usage_data.append({
                'product_id': recipe.product.id,
                'product_name': recipe.product.name,
                'material_id': material.id,
                'material_name': material.name,
                'consumption_rate': float(recipe.consumption_rate),
                'waste_factor': float(recipe.waste_factor),
                'total_consumption': float(recipe.consumption_rate * (1 + recipe.waste_factor)),
                'can_produce': can_produce,
                'unit': material.get_unit_display(),
                'material_cost': float(material_cost_per_product),
                'auto_consume': recipe.auto_consume,
            })
        
        return usage_data
    
    @staticmethod
    def generate_reorder_list(master_id):
        """
        Сгенерировать список материалов для заказа
        """
        materials = Material.objects.filter(
            master_id=master_id,
            is_active=True
        ).annotate(
            reorder_quantity=F('min_quantity') * Decimal('2') - F('current_quantity')
        ).filter(
            reorder_quantity__gt=0
        ).order_by('current_quantity')
        
        reorder_list = []
        for material in materials:
            # Рассчитываем рекомендуемое количество для заказа
            suggested_order = max(
                material.min_quantity * Decimal('2') - material.current_quantity,
                material.min_quantity * Decimal('0.5')  # Минимальный рекомендуемый заказ
            )
            
            # Определяем срочность
            if material.current_quantity == 0:
                urgency = 'critical'
                urgency_text = 'Срочно! Нет в наличии'
            elif material.current_quantity <= material.min_quantity * Decimal('0.5'):
                urgency = 'high'
                urgency_text = 'Высокая'
            elif material.current_quantity <= material.min_quantity:
                urgency = 'medium'
                urgency_text = 'Средняя'
            else:
                urgency = 'low'
                urgency_text = 'Низкая'
            
            reorder_list.append({
                'material_id': material.id,
                'material_name': material.name,
                'current': float(material.current_quantity),
                'min': float(material.min_quantity),
                'suggested': float(suggested_order),
                'unit': material.get_unit_display(),
                'price_per_unit': float(material.price_per_unit),
                'total_cost': float(suggested_order * material.price_per_unit),
                'supplier': material.supplier or 'Не указан',
                'contact': material.supplier_contact or 'Не указан',
                'urgency': urgency,
                'urgency_text': urgency_text,
            })
        
        # Сортируем по срочности
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        reorder_list.sort(key=lambda x: urgency_order[x['urgency']])
        
        return reorder_list
    
    @staticmethod
    def get_material_statistics(master_id):
        """
        Получить статистику по материалам
        """
        materials = Material.objects.filter(master_id=master_id, is_active=True)
        
        # Общая стоимость запасов
        total_value_result = materials.aggregate(
            total=Sum(F('current_quantity') * F('price_per_unit'))
        )
        total_value = total_value_result['total'] or Decimal('0')
        
        stats = {
            'total_materials': materials.count(),
            'total_value': total_value,
            'low_stock_count': materials.filter(
                current_quantity__lte=F('min_quantity'),
                current_quantity__gt=0
            ).count(),
            'out_of_stock_count': materials.filter(current_quantity=0).count(),
            'by_unit': {},
        }
        
        # Статистика по единицам измерения
        for unit_code, unit_name in Material.UNIT_CHOICES:
            unit_materials = materials.filter(unit=unit_code)
            if unit_materials.exists():
                total_quantity_result = unit_materials.aggregate(
                    total=Sum('current_quantity')
                )
                total_value_result = unit_materials.aggregate(
                    total=Sum(F('current_quantity') * F('price_per_unit'))
                )
                
                stats['by_unit'][unit_name] = {
                    'count': unit_materials.count(),
                    'total_quantity': float(total_quantity_result['total'] or 0),
                    'total_value': float(total_value_result['total'] or 0),
                }
        
        # Топ-5 самых ценных запасов
        valuable_materials = []
        for material in materials:
            stock_value = material.stock_value
            if stock_value > 0:
                valuable_materials.append({
                    'name': material.name,
                    'value': float(stock_value),
                    'quantity': float(material.current_quantity),
                    'unit': material.get_unit_display(),
                })
        
        valuable_materials.sort(key=lambda x: x['value'], reverse=True)
        stats['top_valuable'] = valuable_materials[:5]
        
        return stats


class InsufficientMaterialError(Exception):
    """Исключение при недостатке материалов"""
    def __init__(self, material_name, required, available):
        self.material_name = material_name
        self.required = required
        self.available = available
        self.message = f"Недостаточно материала '{material_name}'. Требуется: {required}, доступно: {available}"
        super().__init__(self.message)
    
    def __str__(self):
        return self.message