import inspect
from functools import wraps
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from typing import Any, Optional, Dict
import uuid


def catch_errors(func):
    """Decorator that catches errors for both sync and async endpoints."""
    if inspect.iscoroutinefunction(func):
        # For async functions
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:        # Let FastAPI handle its own HTTPExceptions
                raise
            except Exception as e:
                return JSONResponse(status_code=500, content={"detail": str(e)})
        return async_wrapper
    else:
        # For sync functions
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                return JSONResponse(status_code=500, content={"detail": str(e), "success": False, "status": 500})
        return sync_wrapper


def default_success_msg(status_code: int = 200):
    if (status_code == 200):
        return "Request successful"
    elif (status_code == 201):
        return "Resource created successfully"
    elif (status_code == 204):
        return "Resource deleted successfully"


def format_response(data: Any = None,
                    status_code: int = 200,
                    meta: Optional[Dict[str, Any]] = None
                    ) -> JSONResponse:
    """
    Creates a standardized JSON response.

    Args:
        data: The main response data
        status_code: HTTP status code
        meta: Optional metadata (e.g., pagination info)
    """

    content = {
        "success": 200 <= status_code < 300,
        "status": status_code,
        "message": default_success_msg(status_code),
        "data": jsonable_encoder(data),   # make sure data is JSON serializable
    }

    if meta is not None:
        content["meta"] = meta

    return JSONResponse(status_code=status_code, content=content)



def parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if value is None or value == "":
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None