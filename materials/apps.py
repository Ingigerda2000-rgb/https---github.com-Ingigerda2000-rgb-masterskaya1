from django.apps import AppConfig


class MaterialsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'materials'
    verbose_name = 'Материалы'

    def ready(self):
        # Импортируем сигналы для их регистрации
        try:
            import materials.signals
        except ImportError:
            pass