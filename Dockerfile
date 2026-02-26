# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and necessary directories
COPY src/ ./src/
COPY examples/ ./examples/
COPY tests/ ./tests/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the application using Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 src.web.app:app
