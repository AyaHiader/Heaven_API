from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'name', 'email',  'scheduled_date', 'is_verified']
        read_only_fields = ['is_verified']

    def to_representation(self, instance):
        """Custom representation of the notification"""
        representation = super().to_representation(instance)
        representation['status'] = 'Verified' if instance.is_verified else 'Pending'
        return representation