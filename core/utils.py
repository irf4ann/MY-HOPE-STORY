"""
Common utilities for the project
"""
from rest_framework import status
from rest_framework.response import Response


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
