from django.db import models
from django.utils.crypto import get_random_string
from django.utils import timezone
class Notification(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    scheduled_date = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.scheduled_date}"
    
    def generate_verification_token(self):
        """
        Generate a unique verification token
        """
        token = get_random_string(length=32)
        
        # Ensure token uniqueness
        while Notification.objects.filter(verification_token=token).exists():
            token = get_random_string(length=32)
        
        self.verification_token = token
        self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        self.save()
        
        return token
    def save(self, *args, **kwargs):
        if not self.verification_token:  # Only generate if the token is missing
            self.generate_verification_token()
        super().save(*args, **kwargs)
