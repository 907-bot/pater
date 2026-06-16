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
- [ ] Privacy Policy page hosted
- [ ] Terms of Service page hosted
- [ ] Extension icons generated and verified

---

## 0️⃣ EXTENSION FILES OVERVIEW

The Chrome extension includes these files:

| File | Purpose |
|------|---------|
| `manifest.json` | Extension configuration (Manifest V3) |
| `popup.html/js/css` | Main popup UI |
| `sidepanel.html/js/css` | Detailed side panel view |
| `background.js` | Service worker for background tasks |
| `content-script.js` | Product detection on e-commerce sites |
| `onboarding.html` | First-time user onboarding flow |
| `options.html/js` | Settings and configuration page |
| `privacy-policy.html` | Privacy policy page |
| `terms-of-service.html` | Terms of service page |
| `utils/*.js` | API client, storage, and logging utilities |
| `styles/*.css` | Shared CSS design system |
| `icons/*.png` | Extension icons (16, 48, 128, 256px) |

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

### Step 1: Update API URL (Optional - Can be configured in settings)

The extension now supports configurable API URLs through the Settings page. 
Users can change the API endpoint from `https://pater-api-xyz-asia-south1.run.app` 
to your production URL in the extension settings.

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
# 8. Should show onboarding on first install
# 9. Should show product predictions on product pages
```

### Step 3: Create Extension ZIP

```bash
cd extensions

# Remove any temporary files
rm -f *.zip

# Create ZIP file (exclude non-essential files)
zip -r ../pater-extension-v0.1.0.zip . \
  -x "*.DS_Store" \
  -x "*/.DS_Store" \
  -x "*.txt" \
  -x "*/txt/*"

# Verify ZIP contents
unzip -l ../pater-extension-v0.1.0.zip
```

### Step 4: Prepare Chrome Web Store Assets

Create the following assets before submission:

| Asset | Size | Format |
|-------|------|--------|
| Icon (main) | 128x128 px | PNG |
| Screenshots | 1280x800 px (min 2, max 5) | PNG |
| Promo tile | 440x280 px | PNG |
| Small promo tile | 440x280 px | PNG |

**Required for submission:**
- At least 2 screenshots showing the extension in action
- Privacy policy URL (must be publicly accessible)

### Step 5: Submit to Chrome Web Store

1. Go to: https://chrome.google.com/webstore/devconsole
2. Sign in with your Google account
3. Click "Create new item"
4. Upload the ZIP file (`pater-extension-v0.1.0.zip`)
5. Fill in store listing details:
   - **Name:** Pater - Smart Shopping Assistant
   - **Short description:** AI-powered price predictions for smarter shopping
   - **Long description:** Detailed description of features
   - **Category:** Shopping
   - **Language:** English
6. Upload icons (16, 48, 128 px - already in extension)
7. Upload screenshots
8. Add privacy policy URL (e.g., `https://your-domain.com/privacy-policy.html`)
9. Add store listing contact email
10. Click "Submit for review"

### Step 6: Wait for Review

- Initial review: 1-3 business days
- Updates after rejection: 1-3 business days
- Once approved, extension goes live automatically

---

## 5️⃣ HOST PRIVACY POLICY AND TERMS (Recommended)

For a smoother Chrome Web Store review, host these pages:

1. Upload `extensions/privacy-policy.html` to your website
2. Upload `extensions/terms-of-service.html` to your website
3. Update the links in:
   - `popup.html` (footer links)
   - `sidepanel.html` (settings links)
   - `onboarding.html` (footer links)
   - `options.html` (about section)
4. Update `manifest.json` description with privacy policy URL if needed

```bash
# Example hosting on any web server
cp extensions/privacy-policy.html /var/www/html/
cp extensions/terms-of-service.html /var/www/html/
```

---

## 6️⃣ SETUP MONITORING & LOGGING

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

## 7️⃣ CONTINUOUS DEPLOYMENT (Optional)

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

## 8️⃣ POST-DEPLOYMENT VERIFICATION

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
- [ ] Onboarding flow works on first install
- [ ] Settings page is accessible
- [ ] Notifications work correctly

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

## 9️⃣ SCALING FOR GROWTH

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
✓ Check API_BASE_URL is correct (configure in Settings page)
✓ Verify Cloud Run API is running (gcloud run list)
✓ Check CORS configuration
✓ Look at Chrome DevTools console (Extensions → Service Worker logs)
✓ Try clicking "Test Connection" in Settings
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

### Onboarding Not Showing
```
✓ Extension is freshly installed (check chrome://extensions)
✓ Clear extension storage: chrome.storage.sync.clear()
✓ Reload extension
```

### Service Worker Not Loading
```
✓ Check manifest.json for errors
✓ Verify background.service_worker path
✓ Look at chrome://extensions → Service Worker link
✓ Check for JavaScript errors
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

Your Pater extension is now ready for Chrome Web Store submission!

## 📝 Quick Reference: Extension File Structure

```
extensions/
├── manifest.json          # Extension configuration
├── background.js          # Service worker
├── content-script.js      # Product detection
├── popup.html/js/css      # Main popup UI
├── sidepanel.html/js/css  # Side panel view
├── onboarding.html        # First-time setup
├── options.html/js        # Settings page
├── privacy-policy.html    # Privacy policy
├── terms-of-service.html  # Terms of service
├── icons/                 # Extension icons
├── utils/                 # API client, storage, logger
└── styles/                # Shared CSS design system
```
