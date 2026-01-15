# materials/utils.py
from django.db import models, transaction
from .models import Material, MaterialRecipe, MaterialReservation
from products.models import Product

class MaterialManager:
    """Класс для управления материалами"""
    
    @staticmethod
    @transaction.atomic
    def reserve_for_order(product_id, quantity, order_id):
        """Резервирование материалов для заказа"""
        try:
            product = Product.objects.get(id=product_id)
            unavailable = product.check_material_availability(quantity)
            
            if unavailable:
                return {
                    'success': False,
                    'error': 'Недостаточно материалов',
                    'unavailable': unavailable
                }
            
            reservations = product.reserve_materials_for_order(quantity, order_id)
            
            return {
                'success': True,
                'reservations': len(reservations),
                'order_id': order_id
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @transaction.atomic
    def consume_for_order(order_id):
        """Списание материалов после выполнения заказа"""
        reservations = MaterialReservation.objects.filter(
            order_id=order_id,
            status='reserved'
        )
        
        for reservation in reservations:
            reservation.consume()
        
        return {
            'success': True,
            'consumed': reservations.count()
        }
    
    @staticmethod
    @transaction.atomic
    def release_for_order(order_id):
        """Освобождение резервирования материалов"""
        reservations = MaterialReservation.objects.filter(
            order_id=order_id,
            status='reserved'
        )
        
        for reservation in reservations:
            reservation.release()
        
        return {
            'success': True,
            'released': reservations.count()
        }
    
    @staticmethod
    def check_product_availability(product_id, quantity=1):
        """Проверка доступности материалов для товара"""
        try:
            product = Product.objects.get(id=product_id)
            unavailable = product.check_material_availability(quantity)
            
            return {
                'available': len(unavailable) == 0,
                'product': product.name,
                'unavailable_materials': unavailable,
                'total_needed': product.calculate_material_cost(quantity)
            }
            
        except Product.DoesNotExist:
            return {
                'available': False,
                'error': 'Товар не найден'
            }
    
    @staticmethod
    def get_material_report(master_id=None):
        """Отчет по материалам"""
        query = Material.objects.all()
        if master_id:
            query = query.filter(master_id=master_id)
        
        materials = query.select_related('master')
        
        # Используем агрегацию для подсчета низкого запаса
        low_stock_count = 0
        materials_list = []
        
        for material in materials:
            is_low_stock = material.is_low_stock()
            if is_low_stock:
                low_stock_count += 1
            
            materials_list.append({
                'id': material.id,
                'name': material.name,
                'current_quantity': float(material.current_quantity),
                'unit': material.get_unit_display(),
                'min_quantity': float(material.min_quantity),
                'is_low_stock': is_low_stock,
                'value': float(material.current_quantity * material.price_per_unit),
                'master': material.master.get_full_name() or material.master.email
            })
        
        # Подсчет общей стоимости
        total_value = sum(item['value'] for item in materials_list)
        
        report = {
            'total_materials': len(materials_list),
            'low_stock': low_stock_count,
            'total_value': total_value,
            'materials': materials_list
        }
        
        return report