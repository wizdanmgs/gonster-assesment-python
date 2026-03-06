from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.repositories.sqlalchemy_user import SqlAlchemyUserRepository
from app.schemas.user import Token
from app.core import security
from app.core.config import settings
from app.core.responses import resp_success
from app.core.messages import MSG_SUCCESS, MSG_CREDENTIALS_INCORRECT, MSG_USER_INACTIVE

router = APIRouter()


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_access_token(
    session: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """OAuth2 compatible token login, getting an access token for future requests."""
    user_repo = SqlAlchemyUserRepository(session)
    user = await user_repo.get_by_email(email=form_data.username)
    if not user or not security.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=MSG_CREDENTIALS_INCORRECT
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=MSG_USER_INACTIVE
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires,
    )

    return resp_success(
        message=MSG_SUCCESS,
        status_code=status.HTTP_200_OK,
        data=Token(
            access_token=access_token,
            token_type="bearer",
        ),
    )
