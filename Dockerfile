FROM python:3.11-slim
 
# Run as a non-root user (a DevSecOps best practice Trivy checks for)
RUN useradd -m -u 1000 appuser
WORKDIR /app
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY costwatch ./costwatch
RUN mkdir -p reports && chown -R appuser:appuser /app
USER appuser
 
EXPOSE 8000
CMD ["uvicorn", "costwatch.main:app", "--host", "0.0.0.0", "--port", "8000"]
