from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def student_timetable(request):
    return render(request, 'timetable/student_timetable.html')
