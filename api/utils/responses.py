"""Common response templates for API endpoints."""

from typing import Any

COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Bad Request",
                },
            },
        },
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not Found",
                },
            },
        },
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "field"],
                            "msg": "Field required",
                            "type": "missing",
                        }
                    ]
                },
            },
        },
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Internal Server Error",
                },
            },
        },
    },
}
