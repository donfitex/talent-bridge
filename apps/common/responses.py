from typing import Any, Optional
from rest_framework.response import Response
from rest_framework import status


class APIResponse(Response):
    """
    Standardized API Response wrapper matching specification:
    {
        "data": <payload>
    }
    """
    def __init__(
        self,
        data: Any = None,
        status_code: int = status.HTTP_200_OK,
        message: Optional[str] = None,
        headers: Optional[dict] = None,
        **kwargs
    ):
        envelope = {"data": data}
        if message:
            envelope["message"] = message
        super().__init__(data=envelope, status=status_code, headers=headers, **kwargs)
