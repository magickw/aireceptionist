"""Global exception handlers to prevent stack trace leakage."""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning("IntegrityError request_id=%s: %s", request_id, exc)
    body = {"detail": "Resource conflict (duplicate or constraint violation)."}
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=409, content=body)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception request_id=%s", request_id)
    body = {"detail": "Internal server error."}
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=500, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
