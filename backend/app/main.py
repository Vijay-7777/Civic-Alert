from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
from pathlib import Path
from .agent import Agent
from .config import USE_LANGCHAIN_AGENT, USE_ADVANCED_AGENT, USE_GEMINI_API
from .db import (
    create_report, 
    fetch_report, 
    update_report_status, 
    list_reports,
    get_user_by_email,
    get_departments
)
# Import RAG sync lazily inside endpoint to avoid heavy deps at import time

app = FastAPI(title="Civic Alert API", description="AI-powered locality assistant + issue-reporting system")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# Agent selection with robust fallbacks
if USE_ADVANCED_AGENT and USE_GEMINI_API:
    try:
        from .agent_advanced import get_advanced_agent
        agent = get_advanced_agent()
        print("✅ Using Advanced Agent (Gemini) with memory and reasoning")
    except Exception as e:
        print(f"⚠️  Failed to initialize Advanced Agent: {e}")
        print("   Falling back to LangChain/basic agent")
        try:
            if USE_LANGCHAIN_AGENT:
                from .agent_langchain import LangChainAgent
                agent = LangChainAgent()
                print("✅ Using LangChain agent (better reasoning)")
            else:
                agent = Agent()
                print("Using basic agent")
        except Exception:
            agent = Agent()
            print("Using basic agent")
elif USE_LANGCHAIN_AGENT:
    try:
        from .agent_langchain import LangChainAgent
        agent = LangChainAgent()
        print("✅ Using LangChain agent (better reasoning)")
    except Exception as e:
        print(f"⚠️  Failed to initialize LangChain agent: {e}")
        print("   Falling back to basic agent")
        agent = Agent()
else:
    agent = Agent()
    print("Using basic agent")

class ChatRequest(BaseModel):
    message: str
    user_location: Optional[Dict[str, float]] = None  # {"lat": 12.9716, "lon": 77.5946}

class ChatResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    intent: Optional[str] = None
    model: Optional[str] = None  # Model being used

class ReportCreateRequest(BaseModel):
    reportId: str
    type: str  # EMERGENCY or NON_EMERGENCY
    title: str
    description: str
    specificType: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image: Optional[str] = None
    isAnonymous: bool = True
    reporterName: Optional[str] = None
    reporterEmail: Optional[str] = None
    reporterPhone: Optional[str] = None
    reporterId: Optional[int] = None
    departmentId: Optional[int] = None
    departmentName: Optional[str] = None

class ReportUpdateRequest(BaseModel):
    status: str  # PENDING, IN_PROGRESS, RESOLVED, DISMISSED

@app.post("/agent", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main agent endpoint - processes user messages and routes to appropriate tools"""
    try:
        # Handle both LangChain and basic agents
        if hasattr(agent, 'process_message'):
            result = agent.process_message(request.message, request.user_location)
        else:
            # Fallback for basic agent
            result = agent.process_message(request.message, request.user_location)
        
        # Ensure data is properly formatted for ChatResponse
        if isinstance(result.get('data'), list):
            result['data'] = {'items': result['data']}
        # Adapt advanced agent output: if success message without data, wrap into data.response
        if result.get('success') and not result.get('data') and result.get('message'):
            result['data'] = {'response': result.get('message')}
            if not result.get('intent'):
                result['intent'] = 'general'
        
        # Add model information
        if not result.get('model'):
            if hasattr(agent, 'model'):
                result['model'] = agent.model
            elif hasattr(agent, 'llm') and hasattr(agent.llm, 'model'):
                result['model'] = agent.llm.model
        
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/create")
async def create_report_endpoint(report_data: ReportCreateRequest):
    """Create a new report - matches frontend API"""
    try:
        payload = report_data.dict()
        report_id = create_report(payload)
        try:
            from .rag import index_issue
            title = payload.get("title") or ""
            description = payload.get("description") or ""
            location = payload.get("location") or ""
            # Index into Qdrant (best-effort; errors ignored)
            if title and description:
                index_issue(report_id, title, description, location)
        except Exception:
            pass
        return {
            "success": True,
            "reportId": report_id,
            "message": "Report created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports")
async def list_reports_endpoint(
    status: Optional[str] = None,
    type: Optional[str] = None,
    reporterUserId: Optional[int] = None,
    reporterEmail: Optional[str] = None,
    departmentName: Optional[str] = None
):
    """List reports with filters - matches frontend API"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if type:
            filters["type"] = type
        if reporterUserId:
            filters["reporterUserId"] = reporterUserId
        if reporterEmail:
            filters["reporterEmail"] = reporterEmail
        if departmentName:
            filters["departmentName"] = departmentName
        
        reports = list_reports(filters)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_id}")
async def get_report_endpoint(report_id: str):
    """Get specific report - matches frontend API"""
    try:
        report = fetch_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/reports/{report_id}")
async def update_report_endpoint(report_id: str, update_data: ReportUpdateRequest):
    """Update report status - matches frontend API"""
    try:
        success = update_report_status(report_id, update_data.status)
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"success": True, "message": "Report updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/departments")
async def get_departments_endpoint():
    """Get all departments - matches frontend API"""
    try:
        departments = get_departments()
        return departments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync-qdrant")
async def sync_qdrant_endpoint():
    """Sync database reports to Qdrant for vector search"""
    try:
        from .rag import sync_reports_to_qdrant
        result = await sync_reports_to_qdrant()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Civic Alert API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Civic Alert API",
        "version": "1.0.0",
        "endpoints": ["/agent", "/api/reports/create", "/api/reports", "/api/departments", "/api/sync-qdrant", "/", "/health"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

