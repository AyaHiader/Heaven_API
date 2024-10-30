from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    # Essential fields to display in the list view
    list_display = ('name', 'email', 'scheduled_date', 'is_verified')
    
    # Simple filters for quick data access
    list_filter = ('is_verified',)
    
    # Basic search functionality
    search_fields = ('name', 'email')
    
    # Make verification token read-only since it's auto-generated
    readonly_fields = ('verification_token',)
    
    # Order by newest first
    ordering = ('-created_at',)
    
    # Simple field organization
    fields = (
        'name',
        'email',
        'scheduled_date',
        'is_verified',
        'verification_token'
    )