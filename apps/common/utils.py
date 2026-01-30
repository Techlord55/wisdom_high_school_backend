# Location: .\apps\common\utils.py
# ==================== apps/common/utils.py ====================
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF."""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'error': True,
            'message': str(exc),
            'details': response.data
        }
        response.data = custom_response
    
    return response


def success_response(data=None, message="Success", status=200):
    """Standard success response format."""
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status)


def error_response(message="Error", errors=None, status=400):
    """Standard error response format."""
    return Response({
        'success': False,
        'message': message,
        'errors': errors
    }, status=status)
