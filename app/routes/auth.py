from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.permissions import require_super_admin
from app.database import get_db
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest, LoginResponse, RefreshTokenRequest, AccessTokenResponse, ChangePasswordRequest
from app.schemas.common_schema import MessageResponse
from app.schemas.user_schema import UserMessageResponse, UserActivationRequest
from app.services.auth_service import register_user, login_user, refresh_access_token, get_my_profile, change_password, set_user_activation
from app.utils.rate_limit import rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserMessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))]
)
def register(data: RegisterRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return register_user(data, current_user, db)


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    return login_user(email=form_data.username, password=form_data.password, db=db)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(data: RefreshTokenRequest, db: Session = Depends(get_db)):

    return refresh_access_token(data.refresh_token, db)


@router.get("/me", response_model=UserMessageResponse)
def me(current_user: User = Depends(get_current_user)):

    return get_my_profile(current_user)


@router.put("/change-password", response_model=MessageResponse)
def update_password(data: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return change_password(current_user, data, db)


@router.put("/{user_id}/activation", response_model=UserMessageResponse, dependencies=[Depends(require_super_admin)])
def update_user_activation(user_id: int, data: UserActivationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return set_user_activation(user_id, data.is_active, current_user, db)