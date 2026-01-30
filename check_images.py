import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from products.models import Product

products = Product.objects.filter(status='active')
print(f'Total active products: {products.count()}')
for p in products:
    img = p.get_main_image()
    has_image = img is not None
    print(f'{p.name}: {has_image}')
    if has_image:
        print(f'  Image URL: {img.url}')
