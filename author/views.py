from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
import uuid
from .models import Notification
from .serializers import NotificationSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class NotificationAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Get all notifications or filtered by verification status",
        manual_parameters=[
            openapi.Parameter(
                'verified',
                openapi.IN_QUERY,
                description="Filter by verification status (true/false)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            )
        ],
        responses={200: NotificationSerializer(many=True)}
    )
    def get(self, request):
        # Get query parameters
        is_verified = request.query_params.get('verified', None)
        
        # Get notifications
        notifications = Notification.objects.all()
        
        # Apply filters if provided
        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            notifications = notifications.filter(is_verified=is_verified)
            
        # Serialize the data
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'message': 'Notifications retrieved successfully',
            'count': notifications.count(),
            'notifications': serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=NotificationSerializer,
        operation_description="Create a new notification",
        responses={
            201: openapi.Response(
                description="Notification created successfully",
                examples={
                    "application/json": {
                        "message": "Please check your email to verify your notification"
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            verification_token = str(uuid.uuid4())
            notification = serializer.save(verification_token=verification_token, is_verified=False)
            verification_link = f"{settings.SITE_URL}/verify/{verification_token}"
            
            send_mail(
                'Verify Your Notification',
                f'Hi {notification.name},\n\nPlease click the following link to verify your notification:\n{verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [notification.email],
                fail_silently=False,
            )
            
            return Response(
                {'message': 'Please check your email to verify your notification'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyNotificationView(APIView):
    @swagger_auto_schema(
        operation_description="Verify a notification using token",
        responses={
            200: openapi.Response(
                description="Notification verified successfully",
                examples={
                    "application/json": {
                        "message": "Notification verified successfully",
                        "status": "success"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid token",
                examples={
                    "application/json": {
                        "message": "Invalid or expired verification token",
                        "status": "error"
                    }
                }
            )
        }
    )
    def get(self, request, token):
        try:
            notification = Notification.objects.get(verification_token=token, is_verified=False)
            notification.is_verified = True
            notification.save()
            
            send_mail(
                'Notification Confirmed',
                f'Hi {notification.name},\n\nYour notification has been successfully verified for {notification.scheduled_date}.',
                settings.DEFAULT_FROM_EMAIL,
                [notification.email],
                fail_silently=False,
            )
            
            return Response({
                "message": "Notification verified successfully",
                "status": "success"
            })
        except Notification.DoesNotExist:
            return Response({
                "message": "Invalid or expired verification token",
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)