FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Run one pass by default; override RUN_ONCE=false for the continuous loop.
ENV RUN_ONCE=false
CMD ["python", "-m", "src.main"]
