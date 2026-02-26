## Deployment to Render

Render offers an easy way to deploy web applications. You can deploy using either the **Web Service** (Native Python) or **Docker** environment.

### Option 1: Native Python (Recommended)

1.  **Connect GitHub:** Connect your GitHub repository to Render.
2.  **Create New Web Service:** Select "Web Service" and choose your repository.
3.  **Use Blueprint (Easiest):** Render will automatically detect the `render.yaml` file and set up the service for you.
4.  **Manual Settings (if not using Blueprint):**
    - **Language:** `Python`
    - **Build Command:** `pip install -r requirements.txt`
    - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 src.web.app:app`
    - **Environment Variables:**
        - `PYTHONPATH`: `src`
        - `PYTHONUNBUFFERED`: `1`

### Option 2: Docker

1.  **Create New Web Service:** Select "Web Service" and choose your repository.
2.  **Language:** Select `Docker`.
3.  **Render will automatically find the `Dockerfile`** and build your image.

---

## Deployment to Google Cloud Run

## Prerequisites

1.  **Google Cloud Account:** Ensure you have an active GCP account.
2.  **Google Cloud SDK (gcloud):** Install and initialize the `gcloud` CLI.
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```
3.  **Enable APIs:** Enable the Cloud Build and Cloud Run APIs for your project.
    ```bash
    gcloud services enable cloudsourcing.googleapis.com run.googleapis.com
    ```

## Deployment Steps

We have provided a script to automate the process:

1.  **Make sure the script is executable:**
    ```bash
    chmod +x scripts/deploy_cloudrun.sh
    ```

2.  **Run the deployment script:**
    ```bash
    ./scripts/deploy_cloudrun.sh
    ```

The script will:
- Build a Docker image from the provided `Dockerfile`.
- Push the image to Google Container Registry (GCR).
- Deploy the image to Google Cloud Run with public access.

## Manual Deployment (Alternative)

If you prefer manual steps:

1.  **Build and Push:**
    ```bash
    gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/algocompiler .
    ```

2.  **Deploy:**
    ```bash
    gcloud run deploy algocompiler \
        --image gcr.io/YOUR_PROJECT_ID/algocompiler \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated
    ```

## Customization

- **Region:** You can change the region in `scripts/deploy_cloudrun.sh` (default is `us-central1`).
- **Memory/CPU:** Cloud Run defaults can be adjusted during deployment if needed.
