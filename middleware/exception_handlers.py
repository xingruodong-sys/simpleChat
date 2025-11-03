import json
from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.helper import Log

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    raw_body = await request.body()
    error_detail = {
        "errors": exc.errors(),
        "raw_body": raw_body.decode(),
        "headers": dict(request.headers)
    }
    Log.info("[422 Error Detail]:", json.dumps(error_detail, indent=2))
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed"}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    Log.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

def register_exception_handlers(app: FastAPI):
    """注册异常处理器"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)