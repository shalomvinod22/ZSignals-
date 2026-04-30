FROM python:3.11-slim

WORKDIR /app

# Install deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest
COPY . .

EXPOSE 8501

# Default command runs Streamlit. Override for cron-style runs:
# docker run ... python scripts/run_pipeline.py
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]