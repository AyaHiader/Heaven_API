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
            expires_at = timezone.now() + timedelta(hours=24)

            notification = serializer.save(
                verification_token=verification_token,
                is_verified=False,
                expires_at=expires_at
            )

            verification_link = f"{settings.SITE_URL}/verify/{verification_token}"

            try:
                send_mail(
                    'Verify Your Notification',
                    f'Hi {notification.name},\n\n'
                    f'Please click the following link to verify your notification:\n'
                    f'{verification_link}\n\n'
                    f'This link will expire in 24 hours.',
                    settings.DEFAULT_FROM_EMAIL,
                    [notification.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email to {notification.email}: {e}")
                return Response(
                    {'message': 'Failed to send verification email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {'message': 'Please check your email to verify your notification'},
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
class VerifyNotificationView(APIView):
    def _get_notification(self, token=None):
        """
        Retrieve a notification by its verification token.
        """
        try:
            return Notification.objects.get(verification_token=token, is_verified=False)
        except Notification.DoesNotExist:
            return None

    def get(self, request, token):
        notification = self._get_notification(token)
        if not notification:
            logger.error(f"Invalid or already used token: {token}")
            return Response({
                "message": "Invalid or already used verification token.",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle token expiration
        if notification.expires_at is None or notification.expires_at < timezone.now():
            new_token = secrets.token_urlsafe(32)
            notification.verification_token = new_token
            notification.expires_at = timezone.now() + timedelta(hours=24)
            notification.save()

            logger.warning(f"Token expired for notification ID {notification.id}. Generated new token.")

            verification_link = f"{settings.SITE_URL}/verify/{new_token}"
            try:
                send_mail(
                    'New Verification Token',
                    f'Hi {notification.name},\n\n'
                    f'Your previous token expired. Please verify using this link:\n{verification_link}\n\n'
                    f'This link expires in 24 hours.',
                    settings.DEFAULT_FROM_EMAIL,
                    [notification.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send new token email for notification ID {notification.id}: {e}")
                return Response({
                    "message": "Token renewed, but failed to send email.",
                    "status": "partial_error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "message": "Token expired. A new link has been sent.",
                "status": "token_renewed"
            }, status=status.HTTP_200_OK)

        # Mark as verified
        notification.is_verified = True
        notification.verification_token = None
        notification.save()

        try:
            send_mail(
                'Notification Confirmed',
                f'Hi {notification.name},\n\n'
                f'Your notification has been verified for {notification.scheduled_date}.',
                settings.DEFAULT_FROM_EMAIL,
                [notification.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation email for notification ID {notification.id}: {e}")

        return Response({
            "message": "Notification verified successfully",
            "status": "success"
        }, status=status.HTTP_200_OK)
