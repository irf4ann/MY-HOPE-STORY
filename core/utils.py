"""
Common utilities for the project
"""
import logging
import time

from django.conf import settings
from django.core.mail import send_mail
from django.db import OperationalError, transaction
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class APIResponse:
    """Standard API response wrapper"""
    
    @staticmethod
    def success(data=None, message='Success', status_code=status.HTTP_200_OK):
        return Response({
            'status': 'success',
            'message': message,
            'data': data,
        }, status=status_code)
    
    @staticmethod
    def error(message='Error', data=None, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            'status': 'error',
            'message': message,
            'data': data,
        }, status=status_code)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def paginate_queryset(queryset, page_size=20):
    """Simple pagination helper"""
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = page_size
    return paginator


def retry_on_db_lock(operation, max_attempts=3, base_delay=0.1):
    """Retry a database write when SQLite temporarily reports a lock."""
    last_error = None
    for attempt in range(max_attempts):
        try:
            with transaction.atomic():
                return operation()
        except OperationalError as exc:
            message = str(exc).lower()
            if 'locked' not in message and 'database is locked' not in message:
                raise
            last_error = exc
            if attempt == max_attempts - 1:
                raise
            time.sleep(base_delay * (attempt + 1))

    if last_error is not None:
        raise last_error

    return None


def send_notification_email(subject, message, recipient):
    """Send an email and return whether it was delivered successfully."""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.exception('Failed to send email to %s', recipient)
        return False
