from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError


class SettingNotFound(Exception):
    pass

class CustomException(HTTPException):
    def __init__(self, message: str, code: int = 400):
        super().__init__(status_code=code, detail=message)

async def CustomExceptionHandle(_: Request, exc: CustomException) -> JSONResponse:
    content = dict(code=exc.status_code, msg=exc.detail, data=None)
    return JSONResponse(content=content, status_code=exc.status_code)


async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    content = dict(
        code=404,
        msg=f"Object has not found, exc: {exc}, query_params: {req.query_params}",
    )
    return JSONResponse(content=content, status_code=404)


async def IntegrityHandle(_: Request, exc: IntegrityError) -> JSONResponse:
    content = dict(
        code=500,
        msg=f"IntegrityError，{exc}",
    )
    return JSONResponse(content=content, status_code=500)


async def HttpExcHandle(_: Request, exc: HTTPException) -> JSONResponse:
    content = dict(code=exc.status_code, msg=exc.detail, data=None)
    return JSONResponse(content=content, status_code=exc.status_code)


async def RequestValidationHandle(_: Request, exc: RequestValidationError) -> JSONResponse:
    # 按照需求，如果缺失身体数据，返回 400
    errors = exc.errors()
    msg = f"RequestValidationError, {exc}"
    code = 422
    
    # 检查是否是缺失特定身体指标
    target_fields = ['height_cm', 'weight_kg', 'gender', 'age']
    for error in errors:
        loc = error.get('loc', [])
        if any(field in loc for field in target_fields):
            code = 400
            msg = f"缺失必填字段: {error.get('loc')[-1]}"
            break
            
    content = dict(code=code, msg=msg, data=None)
    return JSONResponse(content=content, status_code=code)


async def ResponseValidationHandle(_: Request, exc: ResponseValidationError) -> JSONResponse:
    content = dict(code=500, msg=f"ResponseValidationError, {exc}")
    return JSONResponse(content=content, status_code=500)
