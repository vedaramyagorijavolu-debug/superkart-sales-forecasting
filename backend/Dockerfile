FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first so dependency installation is cached across code edits
COPY requirements.txt .

# Install dependencies without cache to keep the image compact
RUN pip install --no-cache-dir -r requirements.txt

# Copy app.py, superkart_sales_model.joblib, and any remaining backend files
COPY . .

# Expose Flask/Gunicorn port
EXPOSE 7860

# Start Gunicorn serving Flask instance `superkart_api` from `app.py`
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "app:superkart_api"]
