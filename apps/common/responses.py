from typing import Any

from rest_framework import status
from rest_framework.response import Response


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
        message: str | None = None,
        headers: dict | None = None,
        **kwargs,
    ):
        envelope = {"data": data}
        if message:
            envelope["message"] = message
        super().__init__(data=envelope, status=status_code, headers=headers, **kwargs)
