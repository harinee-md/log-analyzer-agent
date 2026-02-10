# Environment Setup Guide

## Setting Up Your API Key

The Log Analyzer Agent uses Google Gemini for LLM-based metrics evaluation. You need to configure your API key.

### Step 1: Get Your API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### Step 2: Create `.env` File

1. Navigate to the `backend/` directory
2. Copy the example file:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and replace `your-api-key-here` with your actual API key:
   ```
   GOOGLE_API_KEY=AIzaSyC...your-actual-key
   ```

### Step 3: Verify Configuration

Run the backend server:
```bash
cd backend
python run.py
```

Check the health endpoint:
```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "api_key_configured": true
}
```

## Current Setup

**Your app is currently working** because the `GOOGLE_API_KEY` is set as a **system environment variable**. However, using a `.env` file is recommended for:

- ✅ Better security (not in system-wide env)
- ✅ Easier to manage per-project
- ✅ Automatically ignored by git
- ✅ Team collaboration (each dev has their own key)

## Troubleshooting

### "GOOGLE_API_KEY not configured" Error

If you see this error:
1. Make sure `.env` file exists in `backend/` directory
2. Check that the file contains `GOOGLE_API_KEY=your-key`
3. Restart the backend server (Ctrl+C and run `python run.py` again)

### API Key Not Loading

The app loads environment variables in this order:
1. `.env` file (via `python-dotenv`)
2. System environment variables
3. If neither exists → Error

To check if your system env var is set:
```bash
# Windows PowerShell
echo $env:GOOGLE_API_KEY

# Windows CMD
echo %GOOGLE_API_KEY%

# Linux/Mac
echo $GOOGLE_API_KEY
```

## Security Best Practices

- ✅ Never commit `.env` to git (already in `.gitignore`)
- ✅ Never share your API key publicly
- ✅ Rotate keys periodically
- ✅ Use different keys for dev/prod environments
