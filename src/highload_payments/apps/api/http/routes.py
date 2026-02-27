from fastapi import APIRouter


router = APIRouter()


@router.get("/healthcheck")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

