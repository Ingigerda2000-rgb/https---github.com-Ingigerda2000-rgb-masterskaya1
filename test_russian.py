import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'masterskaya.settings')
django.setup()

from django.utils.translation import gettext as _

print("Проверка перевода:")
print(_("Username"))
print(_("Password"))
print(_("Email address"))