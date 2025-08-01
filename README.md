# VideoSplice

AI-powered video editing tool that automatically extracts and labels representative frames from videos.

## Recent Fixes (Latest Deployment)

### CORS and Deployment Issues Fixed

- **Fixed startup command mismatch** between `render.yaml` and `start.sh`
- **Improved CORS configuration** with additional local development URLs
- **Enhanced error handling** in status endpoint with better progress tracking
- **Added environment variable support** for Render deployment
- **Improved logging** for better debugging

### CORS Configuration

- Added support for both `videosplicesite.onrender.com` and `videosplice.onrender.com`
- Added local development URLs (`localhost:5173`, `localhost:3000`, `localhost:8000`)
- Improved CORS headers configuration with proper preflight handling

### Missing HF API Token

- Made the application start gracefully without the Hugging Face API token
- Added proper error handling for missing tokens
- Frame labeling will be skipped if no token is provided

### Deployment Configuration

- Updated `render.yaml` with proper startup command and environment variables
- Added health check endpoint for Render monitoring
- Improved error handling and progress tracking

## Environment Variables

Create a `.env` file in the root directory with:

```env
# Hugging Face API Configuration (optional)
HF_API_TOKEN=your_huggingface_token_here
HF_API_URL=https://your-custom-endpoint.com/pipeline/feature-extraction/openai/clip-vit-base-patch32

# Backend URL for testing (optional)
BACKEND_URL=https://videosplice.onrender.com
```

### Setting up Environment Variables

```bash
# Check current environment
cd backend
python setup_env.py

# Create .env template
python setup_env.py create
```

## Testing

### Test Backend Deployment

```bash
cd backend
python test_deployment.py
```

### Test Backend Startup

```bash
cd backend
python test_startup.py
```

### Test API Endpoints

```bash
cd backend
python test_api.py
```

### Test CORS Configuration

```bash
cd backend
python test_cors.py
```

## Deployment

1. Push changes to your repository
2. Render will automatically deploy using the `render.yaml` configuration
3. The backend will be available at `https://videosplice.onrender.com`
4. The frontend will be available at `https://videosplicesite.onrender.com`

### Deployment Configuration

- The backend runs from the `backend/` directory
- Uses `python -m uvicorn app:app` to start the FastAPI server
- Health check endpoint: `/health`
- Environment variables can be set in Render dashboard

## Troubleshooting

### 502 Bad Gateway

**Symptoms**: Frontend shows "Status check error" and "Failed to fetch"

**Solutions**:

1. Check if the backend service is running on Render
2. Verify the health check endpoint: `https://videosplice.onrender.com/health`
3. Check Render logs for startup errors
4. Ensure environment variables are properly set in Render dashboard

### CORS Errors

**Symptoms**: "Access to fetch blocked by CORS policy"

**Solutions**:

1. Ensure both frontend and backend URLs are in the CORS origins list
2. Check that the frontend is making requests to the correct backend URL
3. Verify the backend is responding with proper CORS headers

### Processing Stuck

**Symptoms**: Status remains "processing" indefinitely

**Solutions**:

1. Check backend logs for processing errors
2. Verify HF_API_TOKEN is set if frame labeling is needed
3. Check if video file is valid and not corrupted
4. Monitor memory usage on Render (starter plan has limits)

### Environment Variable Issues

**Symptoms**: Application fails to start or missing features

**Solutions**:

1. Set `HF_API_TOKEN` in Render dashboard if you want frame labeling
2. Set `HF_API_URL` if using a custom endpoint
3. Use the setup script: `python backend/setup_env.py`

## Monitoring

### Health Check

Monitor backend health at: `https://videosplice.onrender.com/health`

Expected response:

```json
{
  "status": "healthy",
  "jobs_count": 0
}
```

### Logs

Check Render logs for:

- Startup errors
- Processing errors
- CORS issues
- Memory/performance issues
