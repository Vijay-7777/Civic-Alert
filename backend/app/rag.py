import requests
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from .config import QDRANT_URL, QDRANT_COLLECTION, EMBEDDING_MODEL
from .db import list_reports
import uuid

# Initialize embedding model (lazy loading)
embedding_model = None

def get_embedding_model():
    """Get or initialize the embedding model"""
    global embedding_model
    if embedding_model is None:
        try:
            embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            print(f"Warning: Failed to load embedding model: {e}")
            print("Vector search will be disabled")
            return None
    return embedding_model

# Initialize Qdrant client
qdrant_client = QdrantClient(QDRANT_URL, check_compatibility=False)

def create_embeddings(texts: List[str]) -> List[List[float]]:
    """Create embeddings for given texts"""
    model = get_embedding_model()
    if model is None:
        return [[0.0] * 384] * len(texts)  # Return dummy embeddings
    return model.encode(texts).tolist()

def ensure_collection_exists():
    """Ensure the Qdrant collection exists"""
    try:
        # Check if collection exists
        qdrant_client.get_collection(QDRANT_COLLECTION)
    except Exception:
        # Collection doesn't exist, create it
        try:
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except Exception as e:
            # If creation fails, check if it's because collection already exists
            # This can happen in race conditions
            try:
                qdrant_client.get_collection(QDRANT_COLLECTION)
                # Collection exists, so we're good
                return
            except:
                # If we still can't get it, raise the original error
                print(f"Failed to create Qdrant collection: {e}")
                raise e

def index_issue(issue_id: str, title: str, description: str, location: str):
    """Index an issue in Qdrant"""
    ensure_collection_exists()
    
    # Combine text for embedding
    text = f"{title} {description} {location}"
    embedding = create_embeddings([text])[0]
    
    points = []
    import uuid as _uuid
    # Robust ID: try UUID from reportId, else fallback to UUID5
    pid = None
    try:
        pid = _uuid.UUID(str(issue_id))
    except Exception:
        pid = _uuid.uuid5(_uuid.NAMESPACE_URL, str(issue_id))

    points.append(PointStruct(
        id=pid,
        vector=embedding,
        payload={
            "id": issue_id,
            "reportId": issue_id,
            "title": title,
            "description": description,
            "location": location
        }
    ))
    
    qdrant_client.upsert(collection_name=QDRANT_COLLECTION, points=points, wait=True)

async def sync_reports_to_qdrant():
    """Sync all reports from database to Qdrant"""
    ensure_collection_exists()
    
    try:
        # Ensure embedding model is available
        model = get_embedding_model()
        if model is None:
            return {
                "success": False,
                "error": "embedding_model_unavailable",
                "message": "Embedding model could not be loaded; vector sync is disabled"
            }

        # Get all reports from database
        reports = list_reports()
        
        # Clear existing collection to avoid duplicates
        try:
            qdrant_client.delete_collection(QDRANT_COLLECTION)
            ensure_collection_exists()
        except:
            pass
        
        points = []
        # Index each report
        for report in reports:
            if report.get('title') and report.get('description'):
                # Create a combined content string for embedding
                content = f"Report ID: {report.get('reportId', '')}. Title: {report.get('title', '')}. Description: {report.get('description', '')}. Location: {report.get('location', '')}. Type: {report.get('type', '')} - {report.get('specificType', '')}."
                
                # Generate embedding
                embedding = model.encode(content).tolist()
                
                # Create PointStruct
                # Robust point ID: prefer numeric 'id', else valid UUID, else deterministic UUID5
                rid = report.get('id')
                pid = None
                try:
                    if rid is not None and str(rid).isdigit():
                        pid = int(rid)
                except Exception:
                    pid = None
                if pid is None:
                    repid = str(report.get('reportId', '')).strip()
                    try:
                        pid = uuid.UUID(repid)
                    except Exception:
                        base_name = repid or (str(report.get('title', '')) + '|' + str(report.get('createdAt', '')))
                        pid = uuid.uuid5(uuid.NAMESPACE_URL, base_name)

                points.append(PointStruct(
                    id=pid,
                    vector=embedding,
                    payload=report
                ))
        
        # Batch upsert all points
        if points:
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION,
                points=points,
                wait=True
            )
        
        return {
            "success": True,
            "indexed_count": len(points),
            "message": f"Indexed {len(points)} reports to Qdrant"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to sync reports to Qdrant"
        }

def search_local_issues(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for local issues using vector similarity"""
    ensure_collection_exists()
    
    # Create query embedding
    query_embedding = create_embeddings([query])[0]
    
    # Search in Qdrant with compatibility fallback
    res = None
    try:
        res = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_embedding,
            limit=limit,
            with_payload=True
        )
    except Exception:
        try:
            # Older server versions use `search` API
            res = qdrant_client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_embedding,
                limit=limit,
                query_filter=None
            )
        except Exception:
            res = []
    
    # Format results
    results: List[Dict[str, Any]] = []
    try:
        points = getattr(res, "points", None)
        if points is None and isinstance(res, list):
            # Legacy list of ScoredPoint
            for hit in res:
                payload = getattr(hit, "payload", {}) or {}
                results.append({
                    "id": payload.get("id", payload.get("reportId", "")),
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "location": payload.get("location", ""),
                    "score": getattr(hit, "score", None)
                })
        else:
            points = points or []
            for p in points:
                payload = getattr(p, "payload", {}) or {}
                results.append({
                    "id": payload.get("id", payload.get("reportId", "")),
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "location": payload.get("location", ""),
                    "score": getattr(p, "score", None)
                })
    except Exception:
        pass
    
    # If empty, try legacy search explicitly
    if not results:
        try:
            legacy = qdrant_client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_embedding,
                limit=limit,
                query_filter=None
            )
            for hit in legacy or []:
                payload = getattr(hit, "payload", {}) or {}
                results.append({
                    "id": payload.get("id", payload.get("reportId", "")),
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "location": payload.get("location", ""),
                    "score": getattr(hit, "score", None)
                })
        except Exception:
            pass
    
    return results
