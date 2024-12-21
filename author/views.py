from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
import uuid
import secrets
from datetime import timedelta
from .models import Notification
from .serializers import NotificationSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import logging


# Logger for all classes
logger = logging.getLogger(__name__)


class NotificationListView(APIView):
    """
    Handles GET requests for retrieving notifications.
    """

    @swagger_auto_schema(
        operation_description="Get notifications with optional filtering",
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
        is_verified = request.query_params.get('verified', None)
        notifications = Notification.objects.all()

        if is_verified is not None:
            is_verified = is_verified.lower() == 'true'
            notifications = notifications.filter(is_verified=is_verified)

        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'message': 'Notifications retrieved successfully',
            'count': notifications.count(),
            'notifications': serializer.data
        }, status=status.HTTP_200_OK)


class NotificationCreateView(APIView):
    """
    Handles POST requests for creating notifications.
    """

    @swagger_auto_schema(
        request_body=NotificationSerializer,
        operation_description="Create a new notification with time slot validation",
        responses={
            201: openapi.Response(
                description="Notification created successfully",
                examples={
                    "application/json": {
                        "message": "Notification submitted successfully. Please wait for admin validation."
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            # Validate if the time slot is free
            scheduled_date = serializer.validated_data['scheduled_date']
            # Check if any accepted or pending notifications exist for the scheduled date
            if Notification.objects.filter(scheduled_date=scheduled_date, status__in=['accepted', 'pending']).exists():
                return Response(
                    {"message": "This time slot is already taken or pending. Please choose a different time."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save notification as pending
            serializer.save(status='pending')
            return Response(
                {"message": "Notification submitted successfully. Please wait for admin validation."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationUpdateView(APIView):
    """
    Handles PUT requests for updating notifications.
    """

    @swagger_auto_schema(
        request_body=NotificationSerializer,
        operation_description="Update an existing notification",
        responses={
            200: openapi.Response(
                description="Notification updated successfully",
                examples={
                    "application/json": {
                        "message": "Notification updated successfully"
                    }
                }
            )
        }
    )
    def put(self, request, pk=None):
        try:
            notification = Notification.objects.get(pk=pk)

            if notification.is_verified:
                return Response(
                    {'message': 'Cannot update a verified notification'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = NotificationSerializer(notification, data=request.data, partial=True)
            if serializer.is_valid():
                updated_notification = serializer.save()
                return Response({
                    'message': 'Notification updated successfully',
                    'notification': serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Notification.DoesNotExist:
            return Response(
                {'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class NotificationDeleteView(APIView):
    """
    Handles DELETE requests for deleting notifications.
    """

    @swagger_auto_schema(
        operation_description="Delete a notification",
        responses={
            204: openapi.Response(
                description="Notification deleted successfully"
            )
        }
    )
    def delete(self, request, pk=None):
        try:
            notification = Notification.objects.get(pk=pk)
            notification.delete()
            return Response({'message': 'Notification deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response(
                {'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class NotificationAdminDecisionView(APIView):
    """
    Allows the admin to accept or reject a notification request via API.
    This view will update the status of the notification, but email sending is handled in the Django Admin.
    """

    def post(self, request, pk=None):
        try:
            # Retrieve the notification by its primary key
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response(
                {'message': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure the admin action is valid
        action = request.data.get('action', '').lower()
        if action not in ['accept', 'reject']:
            return Response(
                {'message': "Invalid action. Please use 'accept' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If the action is 'accept', set the notification status to 'accepted'
        if action == 'accept':
            notification.status = 'accepted'
            notification.save()

            return Response(
                {'message': 'Notification accepted successfully.'},
                status=status.HTTP_200_OK
            )

        # If the action is 'reject', set the notification status to 'rejected'
        if action == 'reject':
            notification.status = 'rejected'
            notification.save()

            return Response(
                {'message': 'Notification rejected successfully.'},
                status=status.HTTP_200_OK
            )