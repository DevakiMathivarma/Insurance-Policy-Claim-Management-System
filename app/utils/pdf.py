import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.utils.logger import logger

POLICY_DOCUMENT_DIR = "generated_files/policy_documents"
SETTLEMENT_LETTER_DIR = "generated_files/settlement_letters"

os.makedirs(POLICY_DOCUMENT_DIR, exist_ok=True)
os.makedirs(SETTLEMENT_LETTER_DIR, exist_ok=True)


# generates the policy document pdf, given to the customer once a policy
# is activated
def generate_policy_document_pdf(
    policy_id: int,
    policy_number: str,
    customer_name: str,
    plan_name: str,
    coverage_amount: str,
    premium_amount: str,
    start_date: str,
    end_date: str
) -> str:

    try:

        file_path = os.path.join(POLICY_DOCUMENT_DIR, f"policy_{policy_id}.pdf")

        pdf = canvas.Canvas(file_path, pagesize=A4)

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(1 * inch, 10.5 * inch, "Insurance Policy Document")

        pdf.setFont("Helvetica", 12)

        lines = [
            f"Policy Number: {policy_number}",
            f"Policyholder: {customer_name}",
            f"Plan: {plan_name}",
            f"Coverage Amount: {coverage_amount}",
            f"Premium Amount: {premium_amount}",
            f"Start Date: {start_date}",
            f"End Date: {end_date}"
        ]

        y_position = 9.5 * inch

        for line in lines:

            pdf.drawString(1 * inch, y_position, line)
            y_position -= 0.35 * inch

        pdf.save()

        logger.info(f"Policy document PDF generated : {file_path}")

        return file_path

    except Exception as error:

        logger.error(f"Policy document PDF generation failed for policy {policy_id} : {str(error)}")

        raise


# generates the settlement letter pdf, given to the customer once a
# claim is settled
def generate_settlement_letter_pdf(
    settlement_id: int,
    claim_number: str,
    customer_name: str,
    approved_amount: str,
    settlement_date: str,
    payment_reference: str
) -> str:

    try:

        file_path = os.path.join(SETTLEMENT_LETTER_DIR, f"settlement_{settlement_id}.pdf")

        pdf = canvas.Canvas(file_path, pagesize=A4)

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(1 * inch, 10.5 * inch, "Claim Settlement Letter")

        pdf.setFont("Helvetica", 12)

        lines = [
            f"Claim Number: {claim_number}",
            f"Policyholder: {customer_name}",
            f"Approved Amount: {approved_amount}",
            f"Settlement Date: {settlement_date}",
            f"Payment Reference: {payment_reference}"
        ]

        y_position = 9.5 * inch

        for line in lines:

            pdf.drawString(1 * inch, y_position, line)
            y_position -= 0.35 * inch

        pdf.save()

        logger.info(f"Settlement letter PDF generated : {file_path}")

        return file_path

    except Exception as error:

        logger.error(f"Settlement letter PDF generation failed for settlement {settlement_id} : {str(error)}")

        raise