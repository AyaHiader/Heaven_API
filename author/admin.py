from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import logging

logger = logging.getLogger(__name__)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'status', 'is_verified', 'scheduled_date', 'created_at']
    list_filter = ['status', 'is_verified']
    search_fields = ['name', 'email']

    def send_approval_email(self, notification):
        """
        Sends an approval email to the user when the notification is approved.
        """
        try:
            send_mail(
                'Notification Approved',
                f'Hi {notification.name},\n\nYour notification has been approved for the scheduled time: {notification.scheduled_date}.\n\nThank you!',
                settings.DEFAULT_FROM_EMAIL,
                [notification.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send approval email for notification ID {notification.id}: {e}")

    def send_rejection_email(self, notification):
        """
        Sends a rejection email to the user when the notification is rejected.
        """
        try:
            send_mail(
                'Notification Rejected',
                f'Hi {notification.name},\n\nYour notification has been rejected. Please try scheduling another time.\n\nThank you!',
                settings.DEFAULT_FROM_EMAIL,
                [notification.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send rejection email for notification ID {notification.id}: {e}")

    def save_model(self, request, obj, form, change):
        """
        Override the save method to send an email when a notification's status is changed.
        """
        # Check if the status is 'accepted' and is_verified is True
        if obj.status == 'accepted' and obj.is_verified == True:
            obj.is_verified = True  # Ensure the notification is marked as verified
            obj.save()
            self.send_approval_email(obj)

        # Check if the status is 'rejected' and is_verified is False
        elif obj.status == 'rejected' and obj.is_verified == False:
            obj.is_verified = False  # Ensure the notification is marked as not verified
            obj.save()
            self.send_rejection_email(obj)

        # Save the object (whether accepted or rejected, status has changed)
        super().save_model(request, obj, form, change)

# Register the model in the admin site
admin.site.register(Notification, NotificationAdmin)
