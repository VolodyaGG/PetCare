from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.errors import ErrorResponse

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str = "ok"
    database: str = "ok"


@router.get("/health", response_model=HealthResponse, responses={503: {"model": ErrorResponse}})
def health(request: Request) -> HealthResponse | JSONResponse:
    """Readiness: a successful response requires a working PostgreSQL connection."""
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "database_unavailable", "message": "Database unavailable"}},
        )
    return HealthResponse()
