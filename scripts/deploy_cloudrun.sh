#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="algocompiler"
REGION="us-central1"

echo "Using Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"

# Verify gcloud is installed
if ! command -v gcloud &> /dev/null
then
    echo "gcloud command could not be found. Please install Google Cloud SDK."
    exit 1
fi

# Build and push the image using Cloud Build
echo "Building and pushing image to Google Artifact Registry..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
echo "Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1

echo "Deployment complete!"
