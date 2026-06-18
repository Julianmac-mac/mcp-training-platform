FROM python:3.13-slim

RUN groupadd -r appuser && useradd -r -u 10001 -g appuser appuser
WORKDIR /app

# Default DB connection settings for the MSSQL container on the same Docker network
ENV DB_HOST=mssql
ENV DB_PORT=1433

COPY requirements.txt .
COPY pip.conf /etc/pip.conf
ENV PIP_CONFIG_FILE=/etc/pip.conf
RUN pip install --no-cache-dir -r requirements.txt
RUN rm -f /etc/pip.conf

COPY db.py .
COPY main.py .
COPY mcp.yaml .
COPY namespaces/ ./namespaces/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "main.py"]
