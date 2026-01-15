from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Material
from .utils import MaterialManager

@login_required
def material_report(request):
    """Отчет по материалам для мастера"""
    if request.user.role != 'master':
        return render(request, '403.html', status=403)
    
    report = MaterialManager.get_material_report(request.user.id)
    
    return render(request, 'materials/report.html', {
        'report': report,
        'materials': Material.objects.filter(master=request.user)
    })