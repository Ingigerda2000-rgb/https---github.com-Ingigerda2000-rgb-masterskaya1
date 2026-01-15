from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home_view

urlpatterns = [
       path('admin/', admin.site.urls),
    path('', home_view, name='home'),  # Главная страница = список товаров
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),  # Для URL /products/
    path('cart/', include('cart.urls')),
    path('materials/', include('materials.urls')),
    path('orders/', include('orders.urls')),
    path('reviews/', include('reviews.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)