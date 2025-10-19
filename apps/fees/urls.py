from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student/', views.student_fees, name='student_fees'),
    path('parent/', views.parent_payments, name='parent_payments'),
]
