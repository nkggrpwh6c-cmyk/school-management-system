from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'teachers/dashboard.html')


@login_required
def classes(request):
    return render(request, 'teachers/classes.html')
