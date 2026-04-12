from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        field_path = error["loc"]
        field_name = field_path[-1] if field_path else "field"

        # Convert technical error messages to user-friendly ones
        msg = error["msg"]
        if "field required" in msg:
            user_message = f"{field_name} is required"
        elif "ensure this value" in msg:
            user_message = f"{field_name} value is invalid"
        elif "not a valid" in msg:
            user_message = f"{field_name} format is incorrect"
        elif "string too short" in msg or "string too long" in msg:
            user_message = f"{field_name} length is invalid"
        else:
            user_message = f"{field_name} is invalid"

        error_messages.append(user_message)

    combined_message = ". ".join(error_messages)

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "detail": combined_message,
            "success": False
        }
    )