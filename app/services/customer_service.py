from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.user import User, UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerResponse
from app.utils.hashing import hash_password
from app.utils.logger import logger
from app.utils.pagination import get_pagination, get_offset
from app.utils.redis_cache import get_cache, set_cache, delete_cache

CACHE_TTL = 600


def create_customer(data: CustomerCreate, current_user: User | None, db: Session) -> dict:

    try:

        logger.info(f"Creating customer : {data.email}")

        user_repo = UserRepository(db)
        customer_repo = CustomerRepository(db)
        audit_repo = AuditLogRepository(db)

        # only an insurance agent (or admin) can create a customer on
        # someone else's behalf - self-registration (no logged-in user)
        # is always allowed, same hybrid pattern locked in earlier
        if current_user and current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSURANCE_AGENT):

            logger.warning(f"Customer creation blocked. {current_user.role.value} cannot create a customer for someone else.")

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to create a customer account for someone else.")

        existing_user = user_repo.get_by_email_or_phone(data.email, data.phone)

        if existing_user:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone number already registered.")

        # identification number must be unique - level 3 business rule,
        # friendly pre-check backed by the database's own unique
        # constraint as a backstop
        existing_customer = customer_repo.get_by_identification_number(data.identification_number)

        if existing_customer:

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This identification number is already registered.")

        user = User(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=UserRole.CUSTOMER
        )

        user_repo.add(user)

        db.flush()

        customer = Customer(
            user_id=user.id,
            date_of_birth=data.date_of_birth,
            address=data.address,
            identification_number=data.identification_number,
            occupation=data.occupation,
            created_by_user_id=current_user.id if current_user else None
        )

        customer_repo.add(customer)

        db.flush()

        audit_repo.log(
            user_id=current_user.id if current_user else None,
            action="CREATE",
            entity_type="Customer",
            entity_id=customer.id,
            description=f"Customer registered, self-registered={current_user is None}"
        )

        db.commit()

        customer = customer_repo.get_by_id_with_details(customer.id)

        logger.info(f"Customer created successfully : {customer.id}, self-registered={current_user is None}")

        return {"message": "Customer registered successfully.", "data": customer}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Customer creation failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create customer.")


# get by id - cached (bonus feature, redis)
def get_customer_by_id(customer_id: int, db: Session) -> dict:

    logger.info(f"Fetching customer by id : {customer_id}")

    cache_key = f"customer:{customer_id}"

    cached_customer = get_cache(cache_key)

    if cached_customer:

        logger.info(f"Customer cache hit : {customer_id}")

        return {"message": "Customer fetched successfully.", "data": cached_customer}

    customer_repo = CustomerRepository(db)

    customer = customer_repo.get_by_id_with_details(customer_id)

    if not customer:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

    set_cache(cache_key, CustomerResponse.model_validate(customer).model_dump(mode="json"), expire=CACHE_TTL)

    return {"message": "Customer fetched successfully.", "data": customer}


# level 12 - search by name/email, pagination requirement
def get_all_customers(
    db: Session,
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> dict:

    logger.info("Fetching customers list.")

    customer_repo = CustomerRepository(db)

    sortable_columns = {"created_at": Customer.created_at}

    sort_column = sortable_columns.get(sort_by, Customer.created_at)

    customers, total_records = customer_repo.list_customers(search, sort_column, sort_order, get_offset(page, limit), limit)

    return {"message": "Customers fetched successfully.", "data": customers, "pagination": get_pagination(total_records, page, limit)}


def update_customer(customer_id: int, data: CustomerUpdate, current_user: User, db: Session) -> dict:

    try:

        logger.info(f"Updating customer : {customer_id}")

        customer_repo = CustomerRepository(db)
        audit_repo = AuditLogRepository(db)

        customer = customer_repo.get_by_id_with_details(customer_id)

        if not customer:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        # a customer can only update their own profile, staff can update any
        if current_user.role == UserRole.CUSTOMER and customer.user_id != current_user.id:

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")

        update_data = data.model_dump(exclude_unset=True)

        user_fields = {"full_name", "phone"}

        for key, value in update_data.items():

            if key in user_fields:

                setattr(customer.user, key, value)

            else:

                setattr(customer, key, value)

        audit_repo.log(
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Customer",
            entity_id=customer.id,
            description="Customer profile updated"
        )

        db.commit()

        db.refresh(customer)

        delete_cache(f"customer:{customer_id}")

        logger.info(f"Customer updated successfully : {customer_id}")

        return {"message": "Customer updated successfully.", "data": customer}

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        logger.error(f"Customer update failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to update customer.")