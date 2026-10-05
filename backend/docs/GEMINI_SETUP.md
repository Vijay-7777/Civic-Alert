# Gemini API Integration for Civic Alert

This feature allows you to use Google's Gemini API instead of running local models with Ollama for the Civic Alert chatbot.

## Benefits of Gemini API

- **No local GPU required**: Uses Google's cloud infrastructure
- **Faster response times**: Cloud-based processing
- **Higher quality models**: Access to Google's latest models
- **Better reliability**: No need to manage local model downloads

## Setup Instructions

### 1. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 2. Configure Gemini API

Run the setup script:
```bash
cd backend
python setup_gemini.py
```

This will:
- Prompt for your API key
- Update the `.env` file with your configuration
- Install required dependencies (`google-generativeai`)

### 3. Restart the Backend

```bash
# Stop the current server (Ctrl+C)
# Then restart it
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Switching Between Providers

You can easily switch between Ollama and Gemini API:

### Switch to Gemini API
```bash
python switch_provider.py gemini
```

### Switch to Ollama
```bash
python switch_provider.py ollama
```

### Check Current Provider
```bash
python switch_provider.py
```

## Configuration Options

The following environment variables are available in `.env`:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_actual_api_key_here  # Your Gemini API key
GEMINI_MODEL=gemini-1.5-flash            # Model to use
USE_GEMINI_API=true                       # Enable/disable Gemini API

# Ollama Configuration (for comparison)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=gemma:2b
```

## Available Models

- `gemini-1.5-flash`: Fast, lightweight model (recommended)
- `gemini-1.5-pro`: More capable, slower model
- `gemini-pro`: Legacy model

## Troubleshooting

### Common Issues

1. **"API key is invalid or missing"**
   - Check your API key in `.env`
   - Ensure the key has no extra spaces
   - Verify the key is active in Google AI Studio

2. **"Google Generative AI library not installed"**
   - Run: `pip install google-generativeai>=0.8.0`
   - Or use the setup script to install dependencies

3. **"Quota exceeded"**
   - Check your API usage in Google AI Studio
   - You may need to enable billing for higher limits

4. **Connection issues**
   - Check your internet connection
   - Verify firewall isn't blocking the API calls

### Testing the Configuration

You can test if Gemini API is working by:

1. Start the backend server
2. Open the chatbot in the frontend
3. Send a message like "Hello, how are you?"
4. Check if you get a response

The response should indicate which model is being used in the frontend chat interface.

## Cost Considerations

- Gemini API has a free tier with rate limits
- `gemini-1.5-flash` is more cost-effective for chat applications
- Monitor your usage in Google AI Studio
- Consider switching back to Ollama if costs become a concern

## Performance Comparison

| Feature | Gemini API | Ollama (Local) |
|---------|------------|----------------|
| Setup | Easy (API key) | Complex (model download) |
| Speed | Fast (cloud) | Variable (local hardware) |
| Quality | High | Model-dependent |
| Cost | Pay-per-use | Free (after setup) |
| Privacy | Cloud processing | Fully local |
| Offline | No | Yes |

## Security Notes

- Your API key is stored in `.env` - keep this file private
- Don't commit `.env` to version control
- API calls are sent to Google's servers
- Consider privacy implications for sensitive data
