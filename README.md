# VideoSplice

AI-powered video editing tool that automatically extracts and labels representative frames from videos.

## Recent Fixes (Latest Deployment)

### Memory Optimization for Render Free Plan (512MB Limit)

- **Memory monitoring**: Real-time memory usage tracking with psutil
- **Memory limits**: 450MB limit with 62MB safety buffer
- **Video size limits**: 50MB maximum video file size
- **Batch processing**: Process 3 frames at a time instead of all at once
- **Processing optimization**: Reduced frame rate (0.5 FPS) and clip length (120s)
- **Memory cleanup**: Automatic garbage collection and GPU memory clearing
- **Error handling**: Specific `MemoryLimitExceededError` for memory issues

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

## Memory Optimization Details

### Render Free Plan Limitations
- **Memory limit**: 512MB total RAM
- **Our limit**: 450MB (62MB safety buffer)
- **Video size limit**: 50MB maximum
- **Processing**: Optimized for memory efficiency

### Memory Monitoring Features
- **Real-time tracking**: Monitor memory usage throughout processing
- **Automatic cleanup**: Force garbage collection when memory usage is high
- **Batch processing**: Process frames in small batches to reduce memory spikes
- **GPU memory clearing**: Clear CUDA memory after each frame processing
- **Error prevention**: Stop processing before hitting memory limits

### Processing Optimizations
- **Frame rate**: 0.5 FPS (reduced from 1.0 FPS)
- **Clip length**: 120 seconds maximum (reduced from 240s)
- **Batch size**: 3 frames per batch (instead of processing all at once)
- **Memory checks**: Check memory before and after each processing stage

### Error Handling
- **MemoryLimitExceededError**: Specific error for memory issues
- **File size validation**: Reject videos larger than 50MB
- **Graceful degradation**: Stop processing before server crashes
- **User feedback**: Clear error messages about memory limits

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

### Test Memory Optimization

```bash
cd backend
python test_memory_optimization.py
```

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

### Memory Limit Exceeded

**Symptoms**: "Memory limit exceeded" error or server crashes

**Solutions**:
1. Use smaller video files (under 50MB)
2. Try shorter videos (under 2 minutes)
3. Upgrade to Render Pro for 1GB memory ($7/month)
4. Check memory usage in logs

### 502 Bad Gateway

**Symptoms**: Frontend shows "Status check error" and "Failed to fetch"

**Solutions**:
1. Check if the backend service is running on Render
2. Verify the health check endpoint: `https://videosplice.onrender.com/health`
3. Check Render logs for memory-related errors
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
1. Check backend logs for memory-related errors
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

### Memory Monitoring

The system automatically logs memory usage:
- Before and after each processing stage
- During batch processing
- When memory cleanup is triggered
- When memory limits are exceeded

### Logs

Check Render logs for:
- Memory usage statistics
- Memory limit warnings and errors
- Processing progress with memory checks
- CORS issues
- Startup errors

## Upgrade Options

### Render Pro ($7/month)
- **Memory**: 1GB (2x increase)
- **Video size**: Up to 100MB
- **Processing**: Faster, more reliable

### Render Standard ($25/month)
- **Memory**: 2GB (4x increase)
- **Video size**: Up to 200MB
- **Processing**: Much faster, very reliable

### Alternative Platforms
- **Railway**: 1GB free tier
- **Heroku**: 512MB free tier
- **DigitalOcean App Platform**: 1GB starting tier
