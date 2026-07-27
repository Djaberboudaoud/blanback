import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import users, houses

# ── Create all DB tables (if they do not exist yet) ───────────────────────────
Base.metadata.create_all(bind=engine)

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow Flutter app from any origin
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
# Admin CRUD endpoints  →  /admins/...
# Auth login endpoint   →  /auth/login
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(users.router, prefix="/auth",   tags=["Auth"], include_in_schema=False)

# House CRUD + image upload  →  /houses/...
app.include_router(houses.router, prefix="/houses", tags=["Houses"])


# ── Root ───────────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
