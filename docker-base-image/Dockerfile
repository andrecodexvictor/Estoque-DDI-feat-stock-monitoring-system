# Base image for all Estoque-DDI microservices
# This image contains all shared Python dependencies
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy shared requirements
COPY requirements.txt .

# Install all shared Python dependencies
# This layer will be cached and reused by all services
RUN pip install --no-cache-dir -r requirements.txt

# Set Python unbuffered output for better logging
ENV PYTHONUNBUFFERED=1
