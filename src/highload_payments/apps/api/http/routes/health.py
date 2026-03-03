from fastapi import APIRouter


health_router = APIRouter()


@health_router.get("/healthcheck")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
