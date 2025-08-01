# VideoSplice

AI-powered video editing tool that automatically extracts and labels representative frames from videos.

## Deployment Issues Fixed

### CORS Configuration

- Added support for both `videosplicesite.onrender.com` and `videosplice.onrender.com`
- Added local development URLs
- Improved CORS headers configuration

### Missing HF API Token

- Made the application start gracefully without the Hugging Face API token
- Added proper error handling for missing tokens
- Frame labeling will be skipped if no token is provided

### Deployment Configuration

- Added `render.yaml` for proper Render deployment
- Updated `start.sh` with better directory creation
- Added health check endpoint

## Environment Variables

Create a `.env` file in the root directory with:

```env
# Hugging Face API Configuration (optional)
HF_API_TOKEN=your_huggingface_token_here
HF_API_URL=https://your-custom-endpoint.com/pipeline/feature-extraction/openai/clip-vit-base-patch32
```

## Testing

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

## Deployment

1. Push changes to your repository
2. Render will automatically deploy using the `render.yaml` configuration
3. The backend will be available at `https://videosplice.onrender.com`
4. The frontend will be available at `https://videosplicesite.onrender.com`

### Deployment Configuration

- The backend runs from the `backend/` directory
- Uses `python -m uvicorn app:app` to start the FastAPI server
- Health check endpoint: `/health`

## Troubleshooting

### 502 Bad Gateway

- Check if the backend service is running on Render
- Verify the health check endpoint: `https://videosplice.onrender.com/health`
- Check Render logs for startup errors

### CORS Errors

- Ensure both frontend and backend URLs are in the CORS origins list
- Check that the frontend is making requests to the correct backend URL

### Missing HF Token

- The application will work without the token, but frame labeling will be skipped
- Add the token to Render environment variables for full functionality
