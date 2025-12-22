# Docker + Compose gives you one reproducible command to run everything (frontend, backend, later Postgres)
# On EC2 you’ll deploy by pulling from GitHub and running the same Compose setup—no “works on my machine” issues.

# backend/Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better build caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . /app

EXPOSE 5000

# Run Flask
CMD ["python", "app.py"]