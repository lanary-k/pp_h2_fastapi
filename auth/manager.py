from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin, FastAPIUsers
from .database import User, get_user_db
from .auth import auth_backend


SECRET = "SECRET"


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    auth_backends=[auth_backend],
)

current_user_optional = fastapi_users.current_user(
    optional=True
)

current_user = fastapi_users.current_user()