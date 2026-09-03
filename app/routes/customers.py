from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user, get_current_user_optional
from app.auth.permissions import require_admin_or_agent
from app.database import get_db
from app.models.user import User
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerMessageResponse, CustomerPaginationResponse
from app.services.customer_service import create_customer, get_customer_by_id, get_all_customers, update_customer

router = APIRouter(prefix="/api/v1/customers", tags=["Customer Management"])


# public endpoint - works both ways: no token = self-registration,
# insurance agent/admin token = staff creating one on the customer's behalf
@router.post("", response_model=CustomerMessageResponse, status_code=status.HTTP_201_CREATED)
def create_new_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
):

    return create_customer(data, current_user, db)


@router.get("", response_model=CustomerPaginationResponse, dependencies=[Depends(require_admin_or_agent)])
def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db)
):

    return get_all_customers(db=db, page=page, limit=limit, search=search, sort_by=sort_by, sort_order=sort_order)


@router.get("/{customer_id}", response_model=CustomerMessageResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    return get_customer_by_id(customer_id, db)


@router.put("/{customer_id}", response_model=CustomerMessageResponse)
def update_existing_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return update_customer(customer_id, data, current_user, db)