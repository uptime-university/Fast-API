from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from config import settings

# Auth Scheme
azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=settings.SCOPES,
)


# For FastAPI lifespan (startup)
@asynccontextmanager
async def azure_lifespan(app) -> AsyncGenerator[None, None]:
    await azure_scheme.openid_config.load_config()
    yield
