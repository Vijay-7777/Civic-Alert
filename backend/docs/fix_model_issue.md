# Fix: Model Not Available via API

## Problem
- Model `qwen2.5:3b` shows as installed in `ollama list`
- But API returns 404 "model not found"
- API only shows: `qwen3:4b` and `gemma3:1b`

## Solution Options

### Option 1: Restart Ollama Service (Recommended)
1. Stop Ollama service (if running as service)
2. Restart it:
   ```bash
   # On Windows, restart Ollama from Task Manager or:
   # Stop the service, then start it again
   ```

### Option 2: Use Available Model
Update your `.env` file to use an available model:
```bash
OLLAMA_MODEL=qwen3:4b
# OR
OLLAMA_MODEL=gemma3:1b
```

### Option 3: Re-pull the Model
```bash
ollama pull qwen2.5:3b
# Then restart Ollama service
```

## Quick Fix Script
Run this to automatically use an available model:

```bash
python backend/switch_to_available_model.py
```

