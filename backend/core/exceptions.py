"""Custom exception handler for consistent API error responses"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'success': False,
            'error': {
                'status_code': response.status_code,
                'message': _extract_message(response.data),
                'details': response.data,
            }
        }
        response.data = error_data
    else:
        logger.exception(f"Unhandled exception in {context.get('view')}: {exc}")
        response = Response(
            {
                'success': False,
                'error': {
                    'status_code': 500,
                    'message': 'An internal server error occurred.',
                    'details': str(exc) if False else 'Internal Server Error',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response


def _extract_message(data):
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        return 'Validation error'
    if isinstance(data, list):
        return str(data[0]) if data else 'Error'
    return str(data)
