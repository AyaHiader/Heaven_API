from django.db import models

class Notification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    scheduled_date = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.scheduled_date}"

