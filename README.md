# FastAPI + Azure Entra ID (Single-Tenant) Authentication

A concise, corrected, and more-consistent guide for securing a FastAPI application using Azure Entra ID (formerly Azure AD) with the fastapi-azure-auth library. This README tidies up variable names, adds clear code examples, and fixes formatting and small inaccuracies.

What this project demonstrates
- Secure protected routes (scope-based)
- Public routes
- OAuth2 Authorization Code Flow (PKCE) in Swagger UI
- Clear project structure
- Azure App Registrations (API + Swagger/OpenAPI client)
- CORS and configuration via .env

Project layout
```
/app
 ├── main.py
 ├── config.py
 ├── .env
 ├── auth/
 │     └── azure_auth.py
 ├── routers/
       ├── public.py
       └── protected.py
```

1. Code overview (key snippets)
- config.py — Application settings (pydantic)
```python
from pydantic import BaseSettings, AnyUrl
from typing import List

class Settings(BaseSettings):
    TENANT_ID: str
    APP_CLIENT_ID: str      # Backend (API) app registration client id
    OPENAPI_CLIENT_ID: str  # Swagger/OAuth client id
    SCOPE_NAME: str = "user_impersonation"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000"]

    @property
    def SCOPE_FULL_NAME(self) -> str:
        # api://<APP_CLIENT_ID>/user_impersonation
        return f"api://{self.APP_CLIENT_ID}/{self.SCOPE_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

- auth/azure_auth.py — Azure authentication setup
```python
from fastapi import Security
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from .config import Settings

settings = Settings()

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=[settings.SCOPE_FULL_NAME],  # list of allowed scopes
)
```
Note: A startup lifecycle step is useful to ensure OpenID metadata is fetched on app start. The fastapi-azure-auth docs show how to call the metadata loader at startup.

- routers/public.py
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def public_route():
    return {"message": "Hello, this is a public endpoint."}
```

- routers/protected.py
```python
from fastapi import APIRouter, Security
from auth.azure_auth import azure_scheme
from config import Settings

settings = Settings()
router = APIRouter()

@router.get("/protected")
async def protected_route(user = Security(azure_scheme, scopes=[settings.SCOPE_FULL_NAME])):
    # user is a pydantic model provided by fastapi-azure-auth
    return {"message": "You are authenticated!", "user": user.dict()}
```

- main.py (initialization, lifespan, CORS, Swagger OAuth)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Settings
from routers import public, protected

settings = Settings()
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routers
app.include_router(public.router)
app.include_router(protected.router, prefix="/api")

# configure Swagger UI OAuth2 (so the Authorize button works)
app.swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "clientId": settings.OPENAPI_CLIENT_ID,
    "scopes": [settings.SCOPE_FULL_NAME],
}
```

2. Azure setup (single-tenant)
You must create two App Registrations in the tenant.

A. Backend API app (fastapi-backend)
- Register a new app — name: fastapi-backend
- Supported account types: Single tenant
- Copy:
  - Application (client) ID → APP_CLIENT_ID
  - Directory (tenant) ID → TENANT_ID
- Expose an API
  - Application ID URI: api://<APP_CLIENT_ID>
  - Add a scope:
    - Scope name: user_impersonation
    - Admin consent display name: Access API
    - Admin consent description: Allows user to call the API
    - State: Enabled
  - This creates the scope: api://<APP_CLIENT_ID>/user_impersonation
- Manifest: set `"accessTokenAcceptedVersion": 2` to ensure v2 tokens

B. Swagger / OpenAPI client app (fastapi-openapi-client)
- Register a second app — name: fastapi-openapi-client
- Supported account types: Single tenant
- Redirect URIs → Add platform: Single-page application (SPA)
  - Redirect URI: http://localhost:8000/oauth2-redirect
  - (If using a different URL for docs, update accordingly)
- Copy:
  - Application (client) ID → OPENAPI_CLIENT_ID
- API Permissions
  - Add a permission -> APIs my organization uses -> select fastapi-backend
  - Choose delegated permission: user_impersonation
  - Grant admin consent for your tenant (or ask an admin to grant)
- Manifest: set `"accessTokenAcceptedVersion": 2`

3. .env example
Create an .env file (in /app or project root as configured)
```
TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
APP_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OPENAPI_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# CORS origins as a comma-separated list or configure to parse into list in Settings
BACKEND_CORS_ORIGINS=http://localhost:8000
```
Tip: If you store multiple origins, parse them into a list in Settings or use JSON array syntax.

4. Install dependencies
Recommended install (use a virtualenv)
```
pip install fastapi uvicorn fastapi-azure-auth pydantic-settings python-jose
```
(If you prefer a requirements.txt, add these names there.)

5. Run locally
```
uvicorn app.main:app --reload --port 8000
```
Open:
http://localhost:8000/docs

6. Test authentication in Swagger UI
- Open /docs
- Click Authorize
- The Swagger UI will redirect you to Microsoft Entra ID and perform the Authorization Code flow with PKCE
- After login/consent, Swagger receives an access token
- Try calling the protected endpoint (GET /api/protected)

Example authenticated response:
```json
{
  "message": "You are authenticated!",
  "user": {
    "name": "Lokesh Sharma",
    "email": "lokesh@example.com",
    "roles": [],
    "tid": "tenant-guid",
    "oid": "user-guid"
  }
}
```

7. Notes and troubleshooting
- Ensure both app registrations are single-tenant and in the same tenant.
- Ensure you use the backend APP_CLIENT_ID when creating the scope/expose an API.
- Ensure the Swagger/OpenAPI client app has the delegated permission to the backend API and that admin consent is granted.
- If Swagger fails to obtain a token, check the redirect URI, the client ID set in swagger_ui_init_oauth, and that the OpenAPI client app is configured as an SPA redirect.
- If your tokens lack expected claims, confirm `"accessTokenAcceptedVersion": 2` in the manifest and that your app registration token settings are correct.

Summary
This README was cleaned up to:
- Use consistent setting names (SCOPE_NAME / SCOPE_FULL_NAME)
- Show concrete code snippets for config, auth, routers, and main
- Clarify Azure steps and common pitfalls
- Improve formatting and examples

Next steps
- Review the updated README below and commit it into the repository if it looks good.
- If you want, I can prepare a PR that updates README.md in your repo (I will not push anything unless you ask me to).
