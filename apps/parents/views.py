from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'parents/dashboard.html')


@login_required
def children(request):
    return render(request, 'parents/children.html')
