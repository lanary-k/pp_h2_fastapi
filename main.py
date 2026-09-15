from fastapi import FastAPI
from auth.manager import fastapi_users
from auth.auth import auth_backend
from auth.schemas import UserCreate, UserRead
from functions.router import router as links_router


app = FastAPI()

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(links_router)