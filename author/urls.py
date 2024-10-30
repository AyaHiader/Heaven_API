from django.urls import path
from .views import *

urlpatterns = [
    path('', NotificationAPIView.as_view(), name='notification_form'),
    path('api/notifications/', NotificationAPIView.as_view(), name='create_notification'),
    path('verify/<str:token>/', VerifyNotificationView.as_view(), name='verify_notification'),
]