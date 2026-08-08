FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create upload directories
RUN mkdir -p backend/uploads/assignments backend/uploads/submissions

EXPOSE 8000

# Use gunicorn with app factory pattern; PORT env var set by Railway
CMD gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} --chdir backend "app:create_app()"
