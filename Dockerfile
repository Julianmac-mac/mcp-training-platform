FROM python:3.13-slim

RUN groupadd -r appuser && useradd -r -u 10001 -g appuser appuser
WORKDIR /app

# Default DB connection settings for the MSSQL container on the same Docker network
ENV DB_HOST=mssql
ENV DB_PORT=1433
ENV GO_BASE_PATH=go-dev.finneg.com
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ARG NEXUS_USER
ARG NEXUS_PASSWORD
COPY requirements.txt .
RUN pip config set global.extra-index-url "https://${NEXUS_USER}:${NEXUS_PASSWORD}@nexus.finneg.com/repository/python-dev/simple"
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py .
COPY main.py .
COPY mcp.yaml .
COPY namespaces/ ./namespaces/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "main.py"]
