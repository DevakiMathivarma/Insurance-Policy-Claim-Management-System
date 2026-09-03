import io
from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session, joinedload

from app.models.claim import Claim, ClaimStatus
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus
from app.models.plan import Plan
from app.models.policy import Policy, PolicyStatus
from app.models.settlement import Settlement, SettlementStatus
from app.models.user import User, UserRole
from app.schemas.dashboard_schema import (
    DashboardSummary, PolicyPremiumEntry, CustomerPolicyHistoryEntry, ClaimSettlementEntry,
    AgentPerformanceEntry, MonthlyPremiumCollectionEntry, MonthlyClaimStatisticsEntry,
    ClaimTypeBreakdownEntry, TopPayingCustomerEntry, PolicyStatusDistributionEntry
)
from app.utils.logger import logger

TOP_CUSTOMERS_LIMIT = 10


# ---------------------------------------------------------------------------
# Summary - the 10 single-number metrics
# ---------------------------------------------------------------------------


def get_dashboard_summary(db: Session) -> dict:

    logger.info("Generating dashboard summary.")

    total_customers = db.query(Customer).count()
    active_policies = db.query(Policy).filter(Policy.policy_status == PolicyStatus.ACTIVE).count()
    expired_policies = db.query(Policy).filter(Policy.policy_status == PolicyStatus.EXPIRED).count()

    collected_amounts = db.query(Payment.amount).filter(Payment.status == PaymentStatus.SUCCESS).all()
    total_premium_collected = sum((row[0] for row in collected_amounts), Decimal("0.00"))

    pending_amounts = db.query(Policy.premium_amount).filter(Policy.policy_status == PolicyStatus.PENDING).all()
    pending_premium = sum((row[0] for row in pending_amounts), Decimal("0.00"))

    total_claims = db.query(Claim).filter(Claim.status != ClaimStatus.DRAFT).count()
    approved_claims = db.query(Claim).filter(Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.SETTLED])).count()
    rejected_claims = db.query(Claim).filter(Claim.status == ClaimStatus.REJECTED).count()
    pending_claims = db.query(Claim).filter(Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW, ClaimStatus.DOCUMENTS_REQUIRED])).count()

    settlement_amounts = db.query(Settlement.approved_amount).filter(Settlement.settlement_status == SettlementStatus.COMPLETED).all()
    total_settlement_amount = sum((row[0] for row in settlement_amounts), Decimal("0.00"))

    summary = DashboardSummary(
        total_customers=total_customers,
        active_policies=active_policies,
        expired_policies=expired_policies,
        total_premium_collected=total_premium_collected,
        pending_premium=pending_premium,
        total_claims=total_claims,
        approved_claims=approved_claims,
        rejected_claims=rejected_claims,
        pending_claims=pending_claims,
        total_settlement_amount=total_settlement_amount
    )

    return {"message": "Dashboard summary generated successfully.", "data": summary}


# ---------------------------------------------------------------------------
# The 6 named reports
# ---------------------------------------------------------------------------


def get_policy_premium_report(db: Session) -> dict:

    logger.info("Generating policy-wise premium report.")

    policies = (
        db.query(Policy)
        .options(joinedload(Policy.customer).joinedload(Customer.user), joinedload(Policy.plan))
        .all()
    )

    data = [
        PolicyPremiumEntry(
            policy_id=p.id, policy_number=p.policy_number, customer_name=p.customer.user.full_name,
            plan_name=p.plan.plan_name, premium_amount=p.premium_amount, policy_status=p.policy_status.value
        )
        for p in policies
    ]

    return {"message": "Policy-wise premium report generated successfully.", "data": data}


def get_customer_policy_history_report(db: Session) -> dict:

    logger.info("Generating customer policy history report.")

    customers = db.query(Customer).options(joinedload(Customer.user)).all()

    policy_counts = defaultdict(int)

    for customer_id, in db.query(Policy.customer_id).all():

        policy_counts[customer_id] += 1

    payment_rows = (
        db.query(Policy.customer_id, Payment.amount)
        .select_from(Payment)
        .join(Policy, Payment.policy_id == Policy.id)
        .filter(Payment.status == PaymentStatus.SUCCESS)
        .all()
    )

    premium_totals = defaultdict(lambda: Decimal("0.00"))

    for customer_id, amount in payment_rows:

        premium_totals[customer_id] += amount

    data = [
        CustomerPolicyHistoryEntry(
            customer_id=c.id, customer_name=c.user.full_name, total_policies=policy_counts[c.id], total_premium_paid=premium_totals[c.id]
        )
        for c in customers
        if policy_counts[c.id] > 0
    ]

    return {"message": "Customer policy history report generated successfully.", "data": data}


def get_claim_settlement_report(db: Session) -> dict:

    logger.info("Generating claim settlement report.")

    settlements = (
        db.query(Settlement)
        .options(joinedload(Settlement.claim).joinedload(Claim.customer).joinedload(Customer.user))
        .all()
    )

    data = [
        ClaimSettlementEntry(
            claim_id=s.claim.id, claim_number=s.claim.claim_number, customer_name=s.claim.customer.user.full_name,
            approved_amount=s.approved_amount, settlement_date=str(s.settlement_date) if s.settlement_date else None,
            settlement_status=s.settlement_status.value
        )
        for s in settlements
    ]

    return {"message": "Claim settlement report generated successfully.", "data": data}


def get_agent_performance_report(db: Session) -> dict:

    logger.info("Generating agent performance report.")

    agents = db.query(User).filter(User.role == UserRole.INSURANCE_AGENT).all()

    rows = db.query(Policy.agent_id, Policy.premium_amount).filter(Policy.agent_id.isnot(None)).all()

    stats = defaultdict(lambda: {"count": 0, "total": Decimal("0.00")})

    for agent_id, premium_amount in rows:

        stats[agent_id]["count"] += 1
        stats[agent_id]["total"] += premium_amount

    data = [
        AgentPerformanceEntry(
            agent_id=agent.id, agent_name=agent.full_name, total_policies_sold=stats[agent.id]["count"], total_premium_generated=stats[agent.id]["total"]
        )
        for agent in agents
    ]

    return {"message": "Agent performance report generated successfully.", "data": data}


def get_monthly_premium_collection_report(db: Session) -> dict:

    logger.info("Generating monthly premium collection report.")

    payments = db.query(Payment).filter(Payment.status == PaymentStatus.SUCCESS).all()

    monthly = defaultdict(lambda: Decimal("0.00"))

    for payment in payments:

        month_key = payment.payment_date.strftime("%Y-%m")

        monthly[month_key] += payment.amount

    data = [MonthlyPremiumCollectionEntry(month=month, total_collected=total) for month, total in sorted(monthly.items())]

    return {"message": "Monthly premium collection report generated successfully.", "data": data}


def get_monthly_claim_statistics_report(db: Session) -> dict:

    logger.info("Generating monthly claim statistics report.")

    claims = db.query(Claim).filter(Claim.status != ClaimStatus.DRAFT).all()

    monthly = defaultdict(lambda: {"count": 0, "total": Decimal("0.00")})

    for claim in claims:

        month_key = claim.created_at.strftime("%Y-%m")

        monthly[month_key]["count"] += 1
        monthly[month_key]["total"] += claim.claim_amount

    data = [
        MonthlyClaimStatisticsEntry(month=month, total_claims=values["count"], total_claim_amount=values["total"])
        for month, values in sorted(monthly.items())
    ]

    return {"message": "Monthly claim statistics report generated successfully.", "data": data}


# ---------------------------------------------------------------------------
# Bonus reports
# ---------------------------------------------------------------------------


def get_claim_type_breakdown_report(db: Session) -> dict:

    logger.info("Generating claim type breakdown report.")

    rows = db.query(Claim.claim_type, Claim.claim_amount).filter(Claim.status != ClaimStatus.DRAFT).all()

    stats = defaultdict(lambda: {"count": 0, "total": Decimal("0.00")})

    for claim_type, claim_amount in rows:

        stats[claim_type]["count"] += 1
        stats[claim_type]["total"] += claim_amount

    data = [ClaimTypeBreakdownEntry(claim_type=claim_type, claim_count=values["count"], total_amount=values["total"]) for claim_type, values in stats.items()]

    return {"message": "Claim type breakdown report generated successfully.", "data": data}


def get_top_paying_customers_report(db: Session) -> dict:

    logger.info("Generating top paying customers report.")

    rows = (
        db.query(Policy.customer_id, Payment.amount)
        .select_from(Payment)
        .join(Policy, Payment.policy_id == Policy.id)
        .filter(Payment.status == PaymentStatus.SUCCESS)
        .all()
    )

    totals = defaultdict(lambda: Decimal("0.00"))

    for customer_id, amount in rows:

        totals[customer_id] += amount

    top_customer_ids = sorted(totals.keys(), key=lambda cid: totals[cid], reverse=True)[:TOP_CUSTOMERS_LIMIT]

    customers = db.query(Customer).options(joinedload(Customer.user)).filter(Customer.id.in_(top_customer_ids)).all()

    customer_map = {c.id: c for c in customers}

    data = [
        TopPayingCustomerEntry(customer_id=cid, customer_name=customer_map[cid].user.full_name, total_paid=totals[cid])
        for cid in top_customer_ids
        if cid in customer_map
    ]

    return {"message": "Top paying customers report generated successfully.", "data": data}


def get_policy_status_distribution_report(db: Session) -> dict:

    logger.info("Generating policy status distribution report.")

    policies = db.query(Policy.policy_status).all()

    counts = defaultdict(int)

    for status_value, in policies:

        counts[status_value.value] += 1

    data = [PolicyStatusDistributionEntry(status=status_value, count=count) for status_value, count in counts.items()]

    return {"message": "Policy status distribution report generated successfully.", "data": data}


# ---------------------------------------------------------------------------
# Excel export - bonus feature
# ---------------------------------------------------------------------------


def _build_excel_response(filename: str, headers: list[str], rows: list[list]) -> StreamingResponse:

    workbook = Workbook()

    sheet = workbook.active

    sheet.append(headers)

    for cell in sheet[1]:

        cell.font = Font(bold=True)

    for row in rows:

        sheet.append(row)

    for column_cells in sheet.columns:

        max_length = max((len(str(cell.value)) for cell in column_cells if cell.value is not None), default=10)

        sheet.column_dimensions[column_cells[0].column_letter].width = max_length + 2

    buffer = io.BytesIO()

    workbook.save(buffer)

    buffer.seek(0)

    logger.info(f"Excel export generated : {filename}")

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def export_monthly_premium_collection_excel(db: Session) -> StreamingResponse:

    report = get_monthly_premium_collection_report(db)

    rows = [[entry.month, float(entry.total_collected)] for entry in report["data"]]

    return _build_excel_response("monthly_premium_collection.xlsx", ["Month", "Total Collected"], rows)


def export_agent_performance_excel(db: Session) -> StreamingResponse:

    report = get_agent_performance_report(db)

    rows = [[entry.agent_id, entry.agent_name, entry.total_policies_sold, float(entry.total_premium_generated)] for entry in report["data"]]

    return _build_excel_response("agent_performance.xlsx", ["Agent ID", "Agent Name", "Policies Sold", "Premium Generated"], rows)


def export_customer_policy_history_excel(db: Session) -> StreamingResponse:

    report = get_customer_policy_history_report(db)

    rows = [[entry.customer_id, entry.customer_name, entry.total_policies, float(entry.total_premium_paid)] for entry in report["data"]]

    return _build_excel_response("customer_policy_history.xlsx", ["Customer ID", "Customer Name", "Total Policies", "Total Premium Paid"], rows)