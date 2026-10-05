# Upgrading LLM Model for Better Reasoning

## Current Model
- **Current**: `gemma3:1b` (1 billion parameters)
- **Limitation**: Limited reasoning capabilities

## Recommended Models Under 3B Parameters

### 1. Qwen2.5-3B-Instruct (RECOMMENDED) ⭐
- **Model name**: `qwen2.5:3b`
- **Parameters**: 3B
- **Strengths**: 
  - Excellent reasoning capabilities
  - Multilingual support
  - Great for chat and instruction following
  - Best balance of performance and size
- **Install**: `ollama pull qwen2.5:3b`

### 2. Llama-3.2-3B-Instruct
- **Model name**: `llama3.2:3b`
- **Parameters**: 3B
- **Strengths**:
  - Good reasoning
  - Well-supported by Ollama
  - Fast inference
- **Install**: `ollama pull llama3.2:3b`

### 3. Phi-3-mini (Slightly over 3B)
- **Model name**: `phi3:mini`
- **Parameters**: 3.8B
- **Strengths**:
  - Excellent reasoning (rivals GPT-3.5)
  - Microsoft developed
  - MIT license
- **Install**: `ollama pull phi3:mini`

## How to Upgrade

### Step 1: Install the Model
```bash
# For Qwen2.5-3B (Recommended)
ollama pull qwen2.5:3b

# OR for Llama-3.2-3B
ollama pull llama3.2:3b

# OR for Phi-3-mini
ollama pull phi3:mini
```

### Step 2: Update Configuration

**Option A: Environment Variable (Recommended)**
```bash
# In your .env file or environment
OLLAMA_MODEL=qwen2.5:3b
```

**Option B: Update config.py**
```python
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
```

### Step 3: Restart the Backend
```bash
# Restart your FastAPI server
python -m uvicorn app.main:app --reload
```

## Model Comparison

| Model | Parameters | Reasoning | Speed | Multilingual | License |
|-------|-----------|-----------|-------|--------------|---------|
| Qwen2.5-3B | 3B | ⭐⭐⭐⭐⭐ | Fast | Yes | Apache 2.0 |
| Llama-3.2-3B | 3B | ⭐⭐⭐⭐ | Very Fast | Limited | Llama 3.2 |
| Phi-3-mini | 3.8B | ⭐⭐⭐⭐⭐ | Fast | Limited | MIT |
| Gemma3-1B (current) | 1B | ⭐⭐ | Very Fast | Limited | Gemma |

## Testing the Upgrade

After upgrading, test with these queries:
1. "What's the weather like in Lucknow?" (should extract city name)
2. "Show me local news for Mumbai" (should understand location)
3. "What are the local issues near me?" (should reason about context)

## Troubleshooting

### Model Not Found Error
```bash
# Check if model is installed
ollama list

# If not listed, pull it again
ollama pull qwen2.5:3b
```

### Slow Responses
- Qwen2.5-3B is larger than Gemma3-1B, so responses may be slightly slower
- Consider using `llama3.2:3b` if speed is critical

### Memory Issues
- 3B models require ~4-6GB RAM
- Ensure your system has enough memory
- Consider using `phi3:mini` if memory is limited

## Current Configuration

The system is now configured to:
- Use Qwen2.5-3B by default (best reasoning)
- Automatically detect model type and use correct prompt format
- Optimize settings for reasoning tasks (temperature: 0.7, num_predict: 1024)

