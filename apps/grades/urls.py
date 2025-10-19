from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    path('teacher/', views.teacher_grades, name='teacher_grades'),
]
