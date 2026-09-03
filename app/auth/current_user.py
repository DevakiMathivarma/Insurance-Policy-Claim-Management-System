from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.jwt import verify_token_type

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# same as oauth2_scheme, but doesn't force a token to be present -
# auto_error=False means "just tell me who's logged in, if anyone is" -
# needed for customer self-registration through the same POST /customers
# endpoint an insurance agent also uses
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials."
    )

    try:

        payload = verify_token_type(token, expected_type="access")

        email = payload.get("sub")

        if not email:

            raise credentials_exception

    except JWTError:

        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if not user:

        raise credentials_exception

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated."
        )

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> User | None:

    if not token:

        return None

    try:

        return get_current_user(token=token, db=db)

    except HTTPException:

        return None