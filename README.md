📘 FastAPI + Azure Entra ID (Single-Tenant) Authentication

Complete Guide with Code Structure & Azure Setup

This project demonstrates secure authentication for a FastAPI application using Azure Entra ID (formerly Azure AD) with the fastapi-azure-auth library.

It includes:

✔️ Secure protected routes
✔️ Public routes
✔️ OAuth2 Authorization Code Flow (PKCE)
✔️ Swagger UI login using Azure
✔️ Proper project structure
✔️ Azure App Registrations (API + Swagger App)
✔️ CORS + configuration management with .env

📁 Project Structure
/app
 ├── main.py
 ├── config.py
 ├── .env
 ├── auth/
 │     └── azure_auth.py
 ├── routers/
       ├── public.py
       └── protected.py

🧩 1. Code Overview
🔹 config.py — Application Settings

Uses pydantic-settings to load environment variables from .env.

Azure Client IDs

Tenant ID

CORS configuration

Scope configuration (auto-generated)

class Settings(BaseSettings):
    OPENAPI_CLIENT_ID: str = ""
    APP_CLIENT_ID: str = ""
    TENANT_ID: str = ""
    SCOPE_DESCRIPTION: str = "user_impersonation"


The scope name is calculated as:

api://<APP_CLIENT_ID>/user_impersonation

🔹 auth/azure_auth.py — Azure Authentication Setup

Creates the SingleTenantAzureAuthorizationCodeBearer object.
This validates access tokens and loads OpenID metadata.

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=settings.SCOPES,
)


Includes a lifespan function so metadata loads at startup.

🔹 routers/public.py

A simple public route:

@router.get("/")
async def public_route():
    return {"message": "Hello, this is a public endpoint."}


No authentication required.

🔹 routers/protected.py

A route that requires Azure login + scopes:

@router.get("/protected")
async def protected_route(user = Security(azure_scheme, scopes=[settings.SCOPE_NAME])):
    return {"message": "You are authenticated!", "user": user.dict()}

🔹 main.py — Application Initialization

Loads lifespan

Enables CORS

Configures Swagger UI OAuth2

Registers routers

Swagger OAuth setup:

swagger_ui_init_oauth={
    "usePkceWithAuthorizationCodeGrant": True,
    "clientId": settings.OPENAPI_CLIENT_ID,
    "scopes": [settings.SCOPE_NAME],
}


This enables “Authorize” button login using Azure.

🔐 2. Azure Setup (Critical Section)

You must create two Azure App Registrations.

🅐 App Registration 1 – Backend API App

This is your FastAPI backend.

Steps:

Go to Azure → Entra ID → App Registrations → New Registration

Name: fastapi-backend

Supported account types:
✔️ Single tenant

Register → Copy:

Application (client) ID → APP_CLIENT_ID

Directory (tenant) ID → TENANT_ID

Expose an API (Important!)

Go to Expose an API

Click Add a scope

Set Application ID URI:

api://<APP_CLIENT_ID>


Add scope:

Field	Value
Scope name	user_impersonation
Admin consent display name	Access API
Admin consent description	Allows user to call the API
State	Enabled

This scope becomes:

api://<APP_CLIENT_ID>/user_impersonation

Manifest Update

Open Manifest → Set:

"accessTokenAcceptedVersion": 2


This ensures v2.0 tokens are issued.

🅑 App Registration 2 – Swagger / OpenAPI Client

Swagger UI needs its own app registration, because users login through Swagger.

Steps:

New registration
Name: fastapi-openapi-client

Supported account types:
✔️ Single tenant

Redirect URIs → Add (SPA):

http://localhost:8000/oauth2-redirect


Copy:

Application (client) ID → OPENAPI_CLIENT_ID

Assign API Permissions

Go to API Permissions → Add a Permission

Select APIs my organization uses

Find fastapi-backend (App #1)

Select user_impersonation scope

Click Grant admin consent

Manifest Update

Set:

"accessTokenAcceptedVersion": 2

🧪 3. .env Configuration

Create the .env file in /app:

TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
APP_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OPENAPI_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

BACKEND_CORS_ORIGINS=http://localhost:8000

🚀 4. Run Locally

Install dependencies:

pip install fastapi uvicorn fastapi-azure-auth pydantic-settings python-jose


Run:

uvicorn app.main:app --reload


Open:

👉 http://localhost:8000/docs

🔓 5. Test Authentication in Swagger UI

Open Swagger at /docs

Click Authorize

Login with Microsoft Entra ID

Azure redirects back to /oauth2-redirect

Swagger obtains an access token

Now call
▶️ GET /protected

You will get a response like:

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

🎉 6. Summary

This project demonstrates:

✔️ Azure Single-Tenant Authentication
✔️ Authorization Code Flow + PKCE
✔️ Protected API routes
✔️ Swagger UI login
✔️ Clean folder structure
✔️ Config handled via .env
✔️ Scopes validated on each request
