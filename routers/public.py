from fastapi import APIRouter

router = APIRouter(tags=["Public"])


@router.get("/")
async def public_route():
    return {"message": "Hello, this is a public endpoint."}
