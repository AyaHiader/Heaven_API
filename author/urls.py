from django.urls import path
from .views import *

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/create/', NotificationCreateView.as_view(), name='notification-create'),
    path('notifications/<int:pk>/update/', NotificationUpdateView.as_view(), name='notification-update'),
    path('notifications/<int:pk>/delete/', NotificationDeleteView.as_view(), name='notification-delete'),
]