# Use a minimal base image with Python installed
FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr so logs show up immediately in Docker/Codespaces
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BACKEND_URL=http://backend:7860

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies if needed (kept minimal for slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the frontend application files
COPY . .

# Expose port 8501 (default Streamlit port)
EXPOSE 8501

# Run the Streamlit app externally accessible on port 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]