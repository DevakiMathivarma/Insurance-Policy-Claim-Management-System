from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.permissions import require_super_admin, require_any_role
from app.database import get_db
from app.models.plan import PlanStatus, PlanType
from app.models.user import User
from app.schemas.common_schema import MessageResponse
from app.schemas.plan_schema import PlanCreate, PlanUpdate, PlanMessageResponse, PlanPaginationResponse
from app.services.plan_service import create_plan, get_plan_by_id, get_all_plans, update_plan, delete_plan

router = APIRouter(prefix="/api/v1/plans", tags=["Insurance Plan Management"])


@router.post("", response_model=PlanMessageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_super_admin)])
def create_new_plan(data: PlanCreate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):

    return create_plan(data, current_user, db)


@router.get("", response_model=PlanPaginationResponse, dependencies=[Depends(require_any_role)])
def list_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    plan_type: PlanType | None = Query(None),
    status_filter: PlanStatus | None = Query(None, alias="status"),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_plans(db=db, page=page, limit=limit, plan_type=plan_type, status_filter=status_filter, search=search, sort_by=sort_by, sort_order=sort_order)


@router.get("/{plan_id}", response_model=PlanMessageResponse, dependencies=[Depends(require_any_role)])
def get_plan(plan_id: int, db: Session = Depends(get_db)):

    return get_plan_by_id(plan_id, db)


@router.put("/{plan_id}", response_model=PlanMessageResponse, dependencies=[Depends(require_super_admin)])
def update_existing_plan(plan_id: int, data: PlanUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):

    return update_plan(plan_id, data, current_user, db)


@router.delete("/{plan_id}", response_model=MessageResponse, dependencies=[Depends(require_super_admin)])
def remove_plan(plan_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):

    return delete_plan(plan_id, current_user, db)