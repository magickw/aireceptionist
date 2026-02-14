"""
Knowledge Base API Endpoints

Provides endpoints for:
- Document upload and management
- Semantic search across knowledge base
- Document CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import io

from app.api import deps
from app.services.knowledge_base import knowledge_base_service


router = APIRouter()


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Upload a document to the knowledge base.
    
    Supported file types: txt, md, json
    
    Returns document ID and processing status.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Decode content based on file type
        file_name = file.filename
        file_type = file_name.split('.')[-1].lower() if '.' in file_name else 'txt'
        
        if file_type == 'txt':
            text_content = content.decode('utf-8')
        elif file_type == 'md':
            text_content = content.decode('utf-8')
        elif file_type == 'json':
            # Parse JSON and extract text fields
            json_data = json.loads(content.decode('utf-8'))
            text_content = json.dumps(json_data, indent=2)
        else:
            # Try to decode as text
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_type}. Supported types: txt, md, json"
                )
        
        # Create and process document
        document = await knowledge_base_service.create_document(
            business_id=business_id,
            file_name=file_name,
            file_type=file_type,
            content=text_content,
            db=db
        )
        
        return {
            "success": True,
            "document_id": document.id,
            "file_name": document.file_name,
            "status": document.status,
            "message": "Document uploaded and processing started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/text")
async def add_text_document(
    title: str = Form(...),
    content: str = Form(...),
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Add a text document to the knowledge base.
    
    Useful for adding FAQs, policies, or other text content directly.
    """
    try:
        document = await knowledge_base_service.create_document(
            business_id=business_id,
            file_name=f"{title}.txt",
            file_type="txt",
            content=content,
            db=db
        )
        
        return {
            "success": True,
            "document_id": document.id,
            "file_name": document.file_name,
            "status": document.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 20
):
    """
    List all documents in the knowledge base.
    """
    try:
        documents = knowledge_base_service.list_documents(
            business_id=business_id,
            db=db,
            skip=skip,
            limit=limit
        )
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "file_name": doc.file_name,
                    "file_type": doc.file_type,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                }
                for doc in documents
            ],
            "total": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Get a specific document details.
    """
    try:
        document = knowledge_base_service.get_document(
            document_id=document_id,
            business_id=business_id,
            db=db
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks count
        chunks_count = len(document.chunks) if document.chunks else 0
        
        return {
            "id": document.id,
            "file_name": document.file_name,
            "file_type": document.file_type,
            "status": document.status,
            "chunks_count": chunks_count,
            "error_message": document.error_message,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Delete a document from the knowledge base.
    """
    try:
        success = knowledge_base_service.delete_document(
            document_id=document_id,
            business_id=business_id,
            db=db
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_knowledge_base(
    query: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    top_k: int = 5
):
    """
    Semantic search across the knowledge base.
    
    Uses Nova Embeddings to find relevant chunks based on semantic similarity.
    """
    try:
        results = await knowledge_base_service.search(
            query=query,
            business_id=business_id,
            db=db,
            top_k=top_k
        )
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_knowledge_base_get(
    query: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    top_k: int = 5
):
    """
    Semantic search (GET method for easier testing).
    """
    return await search_knowledge_base(query, business_id, db, top_k)
