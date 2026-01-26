#!/usr/bin/env python
"""
Скрипт для создания шаблонов изделий для кастомизации
"""
import os
import django
import sys

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from products.models import Product
from custom_orders.models import ProductTemplate

def create_templates():
    """Создание шаблонов для изделий с кастомизацией"""
    customizable_products = Product.objects.filter(can_be_customized=True, status='active')

    print(f"Найдено изделий с кастомизацией: {customizable_products.count()}")

    for product in customizable_products:
        # Проверяем, есть ли уже шаблон
        template, created = ProductTemplate.objects.get_or_create(
            product=product,
            defaults={
                'name': f"Шаблон {product.name}",
                'base_price': product.price,
                'base_production_days': product.production_time_days or 5,
                'configuration': {
                    'sections': [
                        {
                            'id': 'materials',
                            'name': 'Материалы',
                            'type': 'multiple_choice',
                            'required': True,
                            'max_selections': 3,
                            'options': [
                                {'id': 'cotton', 'name': 'Хлопок', 'price': 500, 'additional_days': 1},
                                {'id': 'wool', 'name': 'Шерсть', 'price': 1200, 'additional_days': 2},
                                {'id': 'silk', 'name': 'Шелк', 'price': 800, 'additional_days': 1},
                            ]
                        },
                        {
                            'id': 'size',
                            'name': 'Размер',
                            'type': 'dropdown',
                            'required': True,
                            'options': [
                                {'id': 's', 'name': 'S', 'price': 0, 'additional_days': 0},
                                {'id': 'm', 'name': 'M', 'price': 200, 'additional_days': 0},
                                {'id': 'l', 'name': 'L', 'price': 400, 'additional_days': 1},
                                {'id': 'xl', 'name': 'XL', 'price': 600, 'additional_days': 1},
                            ]
                        },
                        {
                            'id': 'color',
                            'name': 'Цвет',
                            'type': 'color_picker',
                            'required': False,
                            'options': [
                                {'id': 'white', 'name': 'Белый', 'hex': '#FFFFFF', 'price': 0, 'additional_days': 0},
                                {'id': 'black', 'name': 'Черный', 'hex': '#000000', 'price': 0, 'additional_days': 0},
                                {'id': 'red', 'name': 'Красный', 'hex': '#FF0000', 'price': 100, 'additional_days': 0},
                                {'id': 'blue', 'name': 'Синий', 'hex': '#0000FF', 'price': 100, 'additional_days': 0},
                                {'id': 'green', 'name': 'Зеленый', 'hex': '#00FF00', 'price': 100, 'additional_days': 0},
                            ]
                        },
                        {
                            'id': 'personalization',
                            'name': 'Персонализация',
                            'type': 'text_input',
                            'required': False,
                            'placeholder': 'Введите текст для персонализации (например, инициалы, надпись)',
                            'options': []
                        }
                    ]
                }
            }
        )

        if created:
            print(f"✓ Создан шаблон для изделия: {product.name}")
        else:
            print(f"✓ Шаблон уже существует для изделия: {product.name}")

if __name__ == '__main__':
    create_templates()
    print("\nГотово! Шаблоны изделий созданы.")
