from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_admin_or_agent, require_any_role
from app.database import get_db
from app.models.plan import PlanType
from app.models.policy import PolicyStatus
from app.models.user import User
from app.schemas.policy_schema import PolicyCreate, PolicyUpdate, PolicyMessageResponse, PolicyPaginationResponse
from app.services.policy_service import create_policy, get_policy_by_id, get_all_policies, update_policy, activate_policy, cancel_policy


from app.services.policy_service import (
    create_policy, get_policy_by_id, get_all_policies, update_policy, activate_policy, cancel_policy,
    renew_policy, get_expiring_policies
)
from app.schemas.policy_schema import PolicyListResponse  


router = APIRouter(prefix="/api/v1/policies", tags=["Policy Management"])


@router.post("", response_model=PolicyMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_policy(data: PolicyCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return create_policy(data, current_user, db)


@router.get("", response_model=PolicyPaginationResponse, dependencies=[Depends(require_any_role)])
def list_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    policy_status: PolicyStatus | None = Query(None),
    plan_type: PlanType | None = Query(None),
    customer_id: int | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_policies(db=db, page=page, limit=limit, policy_status=policy_status, plan_type=plan_type, customer_id=customer_id, sort_by=sort_by, sort_order=sort_order)

@router.get("/expiring", response_model=PolicyListResponse, dependencies=[Depends(require_any_role)])
def list_expiring_policies(days: int = Query(30, ge=1), db: Session = Depends(get_db)):

    return get_expiring_policies(db, days)


@router.get("/{policy_id}", response_model=PolicyMessageResponse, dependencies=[Depends(require_any_role)])
def get_policy(policy_id: int, db: Session = Depends(get_db)):

    return get_policy_by_id(policy_id, db)


@router.put("/{policy_id}", response_model=PolicyMessageResponse)
def update_existing_policy(policy_id: int, data: PolicyUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return update_policy(policy_id, data, current_user, db)


@router.post("/{policy_id}/activate", response_model=PolicyMessageResponse)
def activate_existing_policy(policy_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return activate_policy(policy_id, current_user, db)


@router.post("/{policy_id}/cancel", response_model=PolicyMessageResponse)
def cancel_existing_policy(policy_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return cancel_policy(policy_id, current_user, db)



@router.post("/{policy_id}/renew", response_model=PolicyMessageResponse)
def renew_existing_policy(policy_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_agent)):

    return renew_policy(policy_id, current_user, db)


