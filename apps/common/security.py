from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone


class AuthenticationRateLimitMiddleware:
    """Shared-cache fixed-window limit for authentication endpoints, including HTML login."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and (
            request.path.startswith("/api/v1/auth/")
            or request.path in {"/accounts/login/", "/accounts/register/"}
        ):
            key = "auth-rate:{}:{}".format(
                request.META.get("REMOTE_ADDR", "unknown"), int(timezone.now().timestamp()) // 300
            )
            cache.add(key, 0, timeout=300)
            count = cache.incr(key)
            if count > settings.AUTH_RATE_LIMIT:
                response = JsonResponse(
                    {
                        "error": {
                            "code": "THROTTLED",
                            "message": "Too many attempts. Try again later.",
                        }
                    },
                    status=429,
                )
                response["Retry-After"] = "300"
                return response
        return self.get_response(request)
