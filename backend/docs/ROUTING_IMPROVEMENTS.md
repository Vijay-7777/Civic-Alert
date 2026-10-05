# Agent Routing Improvements

## Overview
The Civic Alert agent now properly reasons about user intents and routes requests to the appropriate tools based on the type of query.

## Intent Routing Logic

### 1. Weather Queries
- **Intent**: `weather`
- **Routes to**: Weather API (weatherapi.com)
- **Examples**:
  - "What's the weather like?"
  - "How's the weather today?"
  - "Weather in Delhi"
- **Response Format**: 
  ```json
  {
    "success": true,
    "data": {
      "temperature": 19.4,
      "feels_like": 19.4,
      "humidity": 45,
      "description": "Sunny",
      "city": "Naini Tal",
      "country": "India"
    },
    "intent": "weather"
  }
  ```

### 2. Local News
- **Intent**: `local_news`
- **Routes to**: Web Search (DuckDuckGo/NewsAPI)
- **Examples**:
  - "Show me local news"
  - "What's happening in my area?"
  - "Local news updates"
- **Features**:
  - Uses user's location coordinates
  - Searches for city and state news
  - Falls back to neighboring areas if no local news found
- **Response Format**:
  ```json
  {
    "success": true,
    "data": [
      {
        "title": "News title",
        "description": "News description",
        "source": "Source name",
        "url": "Article URL",
        "location": "City State"
      }
    ],
    "intent": "news"
  }
  ```

### 3. Local Issues
- **Intent**: `local_issues`
- **Routes to**: Database (Qdrant vector store + SQLite)
- **Examples**:
  - "What are the local issues?"
  - "Report a problem in my area"
  - "Community concerns"
- **Features**:
  - Uses RAG (Retrieval Augmented Generation)
  - Searches for issues based on location proximity
  - Returns relevant local issues from database

### 4. Reports
- **Intent**: `reports` or `track_report`
- **Routes to**: Report Management System
- **Examples**:
  - "Help me report a crime"
  - "Track my report #123"
  - "Report status"
- **Features**:
  - Handles new report submissions
  - Tracks existing reports by ID
  - Provides report assistance

### 5. General Chat
- **Intent**: `general`
- **Routes to**: LLM (Gemini API)
- **Examples**:
  - "Hi"
  - "Thank you"
  - "How are you?"
  - General conversations
- **Features**:
  - Uses separate system prompts for intent analysis vs response generation
  - Provides location-aware responses
  - Handles conversational queries naturally

## Technical Improvements

### Fixed Issues
1. **Regex Pattern Bug**: Fixed weather location extraction that was incorrectly matching "like" as a location
2. **Import Scoping**: Removed duplicate inline imports that caused "referenced before assignment" errors
3. **Response Format Handling**: Updated test scripts to handle different response formats for each intent

### Code Changes
1. **agent.py**:
   - Updated regex patterns for location extraction
   - Added `reverse_geocode` and `geocode_location` to main imports
   - Removed inline imports to fix scoping issues
   - Separated system prompts for intent analysis and response generation

2. **tools.py**:
   - `reverse_geocode` function properly defined at the beginning
   - Weather API integration working correctly
   - Local news fetching from web sources

## Testing
Created comprehensive test scripts:
- `test_routing.py` - Tests all intent routing
- `test_multiple.py` - Tests multiple message types
- `test_local_news.py` - Tests news functionality
- `test_weather.py` - Tests weather API

## Usage
The agent now intelligently routes requests based on user intent:
- Location-based queries (weather, news, issues) use the user's coordinates
- General queries are handled by the LLM with context awareness
- Each intent returns appropriate data format for the frontend to display
