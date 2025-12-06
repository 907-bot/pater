# 🚀 PATER - DEPLOYMENT GUIDE

**Complete guide to deploy Pater to production**

---

## 📋 Pre-Deployment Checklist

- [ ] All code committed to GitHub
- [ ] Environment variables configured (.env created from .env.example)
- [ ] MongoDB Atlas cluster created and connection string verified
- [ ] Docker installed and tested locally
- [ ] Google Cloud project created and APIs enabled
- [ ] All tests passing locally
- [ ] Extension tested with load unpacked
- [ ] API responding correctly locally

---

## 1️⃣ DEPLOY MONGODB ATLAS

### Step 1: Create Free Cluster

```bash
# Go to https://www.mongodb.com/cloud/atlas
# 1. Sign up or login
# 2. Create organization "pater"
# 3. Create project "pater"
# 4. Build Database → M0 Free tier
# 5. Provider: AWS, Region: ap-south-1
# 6. Cluster name: pater-cluster
# 7. Click Create (wait 5-10 min)
```

### Step 2: Configure Cluster

```bash
# After cluster created:
# 1. Click "Connect"
# 2. Choose "Drivers" → Python
# 3. Copy connection string:
#    mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/

# Create database user:
# 1. Click "Database Access"
# 2. "Add New Database User"
# 3. Username: pater_admin
# 4. Password: Auto-generate (save it!)
# 5. Database User Privileges: "Built-in Role: Atlas admin"
# 6. Click "Add User"

# Whitelist IP (for development):
# 1. Click "Network Access"
# 2. "Add IP Address"
# 3. Enter: 0.0.0.0/0 (allows all, restrict later for production)
# 4. Click "Confirm"

# Create database:
# 1. Click "Collections"
# 2. "Create Database"
# 3. Database name: pater
# 4. Collection name: products
# 5. Click "Create"
```

### Step 3: Save Connection String

```bash
# Your connection string:
MONGODB_URL=mongodb+srv://pater_admin:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/pater?retryWrites=true&w=majority

# Save to .env file:
echo "MONGODB_URL=..." >> .env
```

---

## 2️⃣ CONTAINERIZE BACKEND

### Step 1: Create Dockerfile (if not exists)

File: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY backend/ .
COPY ml/models/ ./ml/models/

RUN useradd -m -u 1000 pater
USER pater

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Build Docker Image Locally

```bash
cd backend

# Build image
docker build -t pater-api:latest .

# Test locally
docker run -p 8000:8000 \
  -e MONGODB_URL="your_mongodb_url" \
  pater-api:latest

# In another terminal, test:
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

---

## 3️⃣ DEPLOY TO GOOGLE CLOUD RUN

### Step 1: Setup GCP

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Initialize gcloud
gcloud init

# Select your project: pater-ai
gcloud config set project pater-ai

# Configure Docker
gcloud auth configure-docker

# Verify
gcloud auth list
```

### Step 2: Push Docker Image to GCR

```bash
# Set project ID
export PROJECT_ID=$(gcloud config get-value project)

# Tag image
docker tag pater-api:latest gcr.io/$PROJECT_ID/pater-api:latest

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/pater-api:latest

# Verify image was pushed
gcloud container images list
```

### Step 3: Deploy to Cloud Run

```bash
# Deploy
gcloud run deploy pater-api \
  --image gcr.io/$PROJECT_ID/pater-api:latest \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars MONGODB_URL="your_mongodb_url" \
  --max-instances 10 \
  --min-instances 1

# You'll get a URL like:
# https://pater-api-xyz-asia-south1.run.app
```

### Step 4: Test Deployed API

```bash
# Get your service URL
export SERVICE_URL=$(gcloud run services describe pater-api --region asia-south1 --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test prediction endpoint
curl -X POST $SERVICE_URL/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "iPhone 15",
    "current_price": 79999,
    "platform": "Amazon",
    "category": "Electronics"
  }'
```

---

## 4️⃣ DEPLOY CHROME EXTENSION

### Step 1: Update API URL in Extension

File: `extension/utils/api-client.js` or `extension/popup.js`

```javascript
// Change from localhost to production URL
const API_BASE_URL = 'https://pater-api-xyz-asia-south1.run.app';
```

### Step 2: Test Locally

```bash
# Load extension from chrome://extensions
# 1. Open Chrome
# 2. Type: chrome://extensions
# 3. Enable "Developer mode"
# 4. Click "Load unpacked"
# 5. Select pater/extension folder
# 6. Visit amazon.in
# 7. Click Pater icon
# 8. Click "Get Prediction"
# 9. Should show: "75% festival probability, 20-35% discount"
```

### Step 3: Create Extension ZIP

```bash
cd extension

# Create ZIP file
zip -r ../pater-extension-v0.1.0.zip .

# Verify ZIP contents
unzip -l ../pater-extension-v0.1.0.zip | head -20

# Should include: manifest.json, popup.html, popup.js, etc.
```

### Step 4: Submit to Chrome Web Store

```bash
# Go to: https://chrome.google.com/webstore/devconsole
# 1. Sign in with Google
# 2. Create new item → Upload ZIP
# 3. Fill in store details:
#    Name: Pater - Smart Shopping Assistant
#    Description: AI-powered price predictions...
#    Category: Shopping
#    Upload icons (16, 48, 128 px)
#    Upload screenshots (1280x800)
# 4. Add privacy policy URL
# 5. Click "Publish"
# 6. Wait 1-3 days for approval
```

---

## 5️⃣ SETUP MONITORING & LOGGING

### Step 1: Enable Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Filter by errors
gcloud logging read "severity=ERROR" --limit 10

# Real-time logs
gcloud logging read "resource.type=cloud_run_revision" --follow
```

### Step 2: Create Monitoring Alerts

```bash
# Go to: https://console.cloud.google.com/monitoring
# 1. Click "Alerting" → "Create Policy"
# 2. Condition 1: CPU usage > 80%
# 3. Condition 2: Error rate > 1%
# 4. Condition 3: Response time > 1s
# 5. Add notification channels (Email, Slack)
# 6. Click "Create Policy"
```

### Step 3: Setup Performance Tracking

```python
# In backend/main.py, add:
from prometheus_client import Counter, Histogram

# Track predictions
predictions_total = Counter(
    'predictions_total',
    'Total predictions made'
)

prediction_latency = Histogram(
    'prediction_latency_seconds',
    'Time taken for predictions'
)

# In your prediction route:
@app.post("/api/predict")
async def predict(request: PredictionRequest):
    with prediction_latency.time():
        result = await get_prediction(request)
        predictions_total.inc()
        return result
```

---

## 6️⃣ CONTINUOUS DEPLOYMENT (Optional)

### Setup GitHub Actions

File: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/
    
    - name: Build Docker image
      run: |
        docker build -t pater-api:${{ github.sha }} backend/
    
    - name: Push to GCR
      run: |
        gcloud auth configure-docker
        docker push gcr.io/${{ secrets.GCP_PROJECT }}/pater-api:${{ github.sha }}
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy pater-api \
          --image gcr.io/${{ secrets.GCP_PROJECT }}/pater-api:${{ github.sha }} \
          --region asia-south1
```

---

## 7️⃣ POST-DEPLOYMENT VERIFICATION

### Checklist

- [ ] Extension loads in Chrome without errors
- [ ] API responds to all endpoints
- [ ] Database queries working
- [ ] Predictions returning correct format
- [ ] Logging showing activity
- [ ] Monitoring alerts configured
- [ ] Health check passing
- [ ] Response time < 500ms
- [ ] Error rate < 1%
- [ ] Users can install from Web Store

### Manual Testing

```bash
# 1. Test health
curl https://pater-api-xyz.run.app/health

# 2. Test prediction
curl -X POST https://pater-api-xyz.run.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Test", "current_price": 1000, "platform": "Amazon", "category": "Test"}'

# 3. Test watchlist
curl https://pater-api-xyz.run.app/api/watchlist

# 4. Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20
```

---

## 🔒 SECURITY HARDENING (For Production)

### Step 1: Restrict IP Access

```bash
# In MongoDB Atlas:
# 1. Network Access
# 2. Remove 0.0.0.0/0
# 3. Add Cloud Run IP ranges:
#    35.198.0.0/16   (Cloud Run us-central1)
#    35.201.0.0/16   (Cloud Run europe-west1)
#    34.96.0.0/13    (Cloud Run asia-south1)
# 4. Save
```

### Step 2: Configure API Authentication

```python
# In backend/main.py, add API key check:
from fastapi import Header, HTTPException

@app.post("/api/predict")
async def predict(request: PredictionRequest, x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... rest of code
```

### Step 3: Enable CORS Properly

```python
# In backend/main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pater-extension-id.chromium.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 4: Setup SSL/TLS

```bash
# Cloud Run auto-provides HTTPS
# All traffic is encrypted by default
# Verify: curl -I https://pater-api-xyz.run.app
```

---

## 📊 SCALING FOR GROWTH

### Vertical Scaling
```bash
# Increase resources on Cloud Run:
gcloud run deploy pater-api \
  --memory 4Gi \
  --cpu 4 \
  --max-instances 50
```

### Horizontal Scaling
```bash
# Set up load balancer:
# Go to Cloud Console → Network Services → Load balancing
# Create new load balancer pointing to Cloud Run service
```

### Database Scaling
```bash
# Upgrade MongoDB:
# M0 → M2 (2GB) - $9/month
# M2 → M5 (5GB) - $25/month
# In MongoDB Atlas console → Clusters → Change plan
```

---

## 🐛 TROUBLESHOOTING

### Extension Won't Connect
```
✓ Check API_BASE_URL is correct
✓ Verify Cloud Run API is running (gcloud run list)
✓ Check CORS configuration
✓ Look at Chrome DevTools console
```

### API Returns 500 Error
```
✓ Check logs: gcloud logging read "severity=ERROR"
✓ Verify MongoDB connection string
✓ Check models are loaded correctly
✓ Verify environment variables set
```

### Slow Response Times
```
✓ Check Cloud Run metrics
✓ Scale up instances (--max-instances)
✓ Optimize MongoDB queries
✓ Add Redis caching layer
```

---

## 📈 Next Steps After Deployment

1. **Monitor metrics** - CPU, memory, latency, errors
2. **Gather user feedback** - Fix issues quickly
3. **Optimize performance** - Reduce prediction latency
4. **Add features** - Based on user requests
5. **Scale infrastructure** - As users grow
6. **Monetize** - Launch freemium model

---

## 🆘 Support

- **Issues**: GitHub Issues
- **Logs**: `gcloud logging read`
- **Monitoring**: Cloud Console
- **Documentation**: See ARCHITECTURE.md

---

**Deployment Checklist Complete! 🚀**

Your Pater extension is now live for users to install!
