from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.material_report, name='material_report'),
]