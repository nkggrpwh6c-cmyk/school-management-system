from django.db import models


class Timetable(models.Model):
    """
    Class timetable model
    """
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
