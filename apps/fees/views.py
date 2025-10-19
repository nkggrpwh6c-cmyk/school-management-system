from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'fees/dashboard.html')


@login_required
def student_fees(request):
    return render(request, 'fees/student_fees.html')


@login_required
def parent_payments(request):
    return render(request, 'fees/parent_payments.html')
