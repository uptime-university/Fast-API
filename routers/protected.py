from fastapi import APIRouter, Security
from auth.azure_auth import azure_scheme
from config import settings

router = APIRouter(tags=["Protected"])


@router.get("/protected")
async def protected_route(user=Security(azure_scheme, scopes=[settings.SCOPE_NAME])):
    return {
        "message": "You are authenticated!",
        "user": user.dict(),
    }
