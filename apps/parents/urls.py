from django.urls import path
from . import views

app_name = 'parents'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('children/', views.children, name='children'),
]
