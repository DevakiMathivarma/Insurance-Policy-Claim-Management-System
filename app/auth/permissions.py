from fastapi import Depends, HTTPException, status

from app.auth.current_user import get_current_user
from app.models.user import User, UserRole


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super Admin access required.")
    return current_user


def require_insurance_agent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.INSURANCE_AGENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insurance Agent access required.")
    return current_user


def require_claims_officer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.CLAIMS_OFFICER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Claims Officer access required.")
    return current_user


def require_finance_officer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.FINANCE_OFFICER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Finance Officer access required.")
    return current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customer access required.")
    return current_user


# admin or insurance agent - the sales/policy side: customers (agent-created
# path), policies, beneficiaries
def require_admin_or_agent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSURANCE_AGENT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Insurance Agent access required.")
    return current_user


# admin or claims officer - the claims-handling side: document
# verification, assessment, approval/rejection
def require_admin_or_claims_officer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.CLAIMS_OFFICER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Claims Officer access required.")
    return current_user


# admin or finance officer - the payout side: settlements
def require_admin_or_finance_officer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.FINANCE_OFFICER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or Finance Officer access required.")
    return current_user


def require_any_role(current_user: User = Depends(get_current_user)) -> User:
    return current_user