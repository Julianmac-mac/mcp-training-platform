FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
       | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
       https://packages.microsoft.com/debian/12/prod bookworm main" \
       > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -u 10001 -g appuser appuser
WORKDIR /app

COPY requirements.txt .
COPY pip.conf /etc/pip.conf
ENV PIP_CONFIG_FILE=/etc/pip.conf
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY mcp.yaml .
COPY namespaces/ ./namespaces/
COPY db_init.sql .
COPY init_db.py .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "python init_db.py && python main.py"]
