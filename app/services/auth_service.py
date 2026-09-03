from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import RegisterRequest, ChangePasswordRequest
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, verify_token_type
from app.utils.logger import logger


# flat hierarchy - all 3 staff roles report directly to super admin, no
# sub-hierarchy like the property platform's facility manager creating staff
def _allowed_roles_for(current_user_role: UserRole) -> list:

    if current_user_role == UserRole.SUPER_ADMIN:

        return [UserRole.INSURANCE_AGENT, UserRole.CLAIMS_OFFICER, UserRole.FINANCE_OFFICER]

    return []


def register_user(data: RegisterRequest, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Registration started : {data.email}, requested role={data.role.value}")

        user_repo = UserRepository(db)
        audit_repo = AuditLogRepository(db)

        allowed_roles = _allowed_roles_for(current_user.role)

        if data.role not in allowed_roles:

            logger.warning(f"Registration blocked. {current_user.role.value} cannot create role {data.role.value}")

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"You are not allowed to create a user with role {data.role.value}.")

        existing_user = user_repo.get_by_email_or_phone(data.email, data.phone)

        if existing_user:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone number already registered.")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role
        )

        user_repo.add(user)

        db.flush()

        audit_repo.log(
            user_id=current_user.id,
            action="CREATE",
            entity_type="User",
            entity_id=user.id,
            description=f"Registered new {data.role.value}"
        )

        db.commit()

        db.refresh(user)

        logger.info(f"User registered successfully : {user.email}, role={user.role.value}")

        return {"message": "User registered successfully.", "data": user}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Registration failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to register user.")


def login_user(email: str, password: str, db: Session) -> dict:

    try:

        logger.info(f"Login attempt : {email}")

        user_repo = UserRepository(db)

        user = user_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        if not user.is_active:

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been deactivated.")

        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})

        logger.info(f"Login successful : {user.email}")

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    except HTTPException:

        raise

    except Exception as error:

        logger.error(f"Login failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to login.")


def refresh_access_token(refresh_token: str, db: Session) -> dict:

    try:

        logger.info("Refresh token requested.")

        user_repo = UserRepository(db)

        try:

            payload = verify_token_type(refresh_token, expected_type="refresh")

        except JWTError:

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

        email = payload.get("sub")

        if not email:

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

        user = user_repo.get_by_email(email)

        if not user or not user.is_active:

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

        access_token = create_access_token(data={"sub": user.email})

        logger.info(f"Access token refreshed : {user.email}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:

        raise

    except Exception as error:

        logger.error(f"Refresh token failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to refresh token.")


def get_my_profile(current_user: User) -> dict:

    return {"message": "Profile fetched successfully.", "data": current_user}


def change_password(current_user: User, data: ChangePasswordRequest, db: Session) -> dict:

    try:

        logger.info(f"Change password started : {current_user.email}")

        if not verify_password(data.current_password, current_user.password_hash):

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")

        if verify_password(data.new_password, current_user.password_hash):

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the current password.")

        current_user.password_hash = hash_password(data.new_password)

        db.commit()

        logger.info(f"Password changed successfully : {current_user.email}")

        return {"message": "Password changed successfully."}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Change password failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to change password.")


def set_user_activation(user_id: int, is_active: bool, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Setting user activation : {user_id}, is_active={is_active}")

        user_repo = UserRepository(db)
        audit_repo = AuditLogRepository(db)

        user = user_repo.get_by_id(user_id)

        if not user:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # a super admin should never be able to accidentally deactivate
        # themselves, locking everyone out of the system
        if user.id == current_user.id:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own activation status.")

        user.is_active = is_active

        audit_repo.log(
            user_id=current_user.id,
            action="ACTIVATE" if is_active else "DEACTIVATE",
            entity_type="User",
            entity_id=user.id,
            description=f"Account {'activated' if is_active else 'deactivated'}"
        )

        db.commit()

        db.refresh(user)

        logger.info(f"User activation updated successfully : {user_id}, is_active={is_active}")

        return {"message": f"User account {'activated' if is_active else 'deactivated'} successfully.", "data": user}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"User activation update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update user activation status.")


def create_default_admin(db: Session) -> None:

    try:

        logger.info("Checking default admin.")

        user_repo = UserRepository(db)

        existing_admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()

        if existing_admin:

            logger.info("Default admin already exists.")

            return

        admin = User(
            full_name="Platform Super Admin",
            email=settings.DEFAULT_ADMIN_EMAIL,
            phone=settings.DEFAULT_ADMIN_PHONE,
            password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )

        user_repo.add(admin)

        db.commit()

        logger.info(f"Default admin created successfully : {settings.DEFAULT_ADMIN_EMAIL}")

    except Exception as error:

        db.rollback()

        logger.error(f"Default admin creation failed : {str(error)}")