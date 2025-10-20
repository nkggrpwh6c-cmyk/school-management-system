from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Health check endpoint for Render deployment
    """
    return JsonResponse({
        'status': 'healthy',
        'message': 'Application is running'
    }, status=200)
