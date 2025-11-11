FROM python:3.11-slim

WORKDIR /app

COPY services/universal_verifier/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH=/app

CMD ["uvicorn", "services.universal_verifier.app:app", "--host", "0.0.0.0", "--port", "8080"]
