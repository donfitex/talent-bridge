import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger("apps.common")


class TalentBridgeAPIException(APIException):
    """Base API Exception for TalentBridge application."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "BAD_REQUEST"
    default_detail = "An invalid operation was requested."

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.default_code = code
        super().__init__(detail=detail, code=self.default_code)


def custom_exception_handler(exc, context):
    """
    Standardizes error responses across all APIs:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable description",
            "details": {...}  # optional field for validation errors
        }
    }
    """
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.db.models.deletion import ProtectedError
    from rest_framework.exceptions import ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(getattr(exc, "message_dict", None) or exc.messages)
    if isinstance(exc, ProtectedError):
        exc = TalentBridgeAPIException(detail="This record is referenced by protected data.", code="RESOURCE_IN_USE", status_code=409)
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, "default_code", getattr(exc, "code", "API_ERROR"))
        if hasattr(error_code, "upper"):
            error_code = error_code.upper()
        else:
            error_code = "VALIDATION_ERROR"

        error_message = ""
        details = None

        if isinstance(response.data, dict):
            if "detail" in response.data:
                error_message = str(response.data["detail"])
            else:
                error_message = "Validation error occurred."
                details = response.data
        elif isinstance(response.data, list):
            error_message = "; ".join([str(item) for item in response.data])
        else:
            error_message = str(response.data)

        custom_data = {
            "error": {
                "code": error_code,
                "message": error_message,
            }
        }
        if details:
            custom_data["error"]["details"] = details

        response.data = custom_data
        return response

    # Unhandled server exceptions
    logger.exception("Unhandled server exception: %s", exc)
    return Response(
        {
            "error": {
                "code": "SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
