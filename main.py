from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from exceptions import PredictionError
from routers.predict import router as predict_router

app = FastAPI(
    title="Ad moderation service",
    description="Проверка объявлений на нарушения.",
    version="0.1.0",
)
app.include_router(predict_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Контракт сервиса требует 400 на неверный вход, FastAPI по умолчанию отдаёт 422.
    return JSONResponse(status_code=400, content={"detail": jsonable_encoder(exc.errors())})


@app.exception_handler(PredictionError)
async def prediction_error_handler(request: Request, exc: PredictionError) -> JSONResponse:
    logger.warning("Ошибка бизнес-логики: {}", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error("Необработанная ошибка")
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})
