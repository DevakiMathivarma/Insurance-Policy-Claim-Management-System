# Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# folders the app writes generated files into - created here so they
# exist even on a completely fresh container
RUN mkdir -p generated_files/policy_documents generated_files/settlement_letters generated_files/claim_uploads logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]