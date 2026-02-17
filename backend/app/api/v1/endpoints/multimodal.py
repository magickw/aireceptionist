"""API endpoints for multimodal file upload and processing"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_db, get_current_active_user
from app.models.models import User
from app.services.multimodal_service import multimodal_service, process_uploaded_file
from pydantic import BaseModel


router = APIRouter()


class MultimodalUploadResponse(BaseModel):
    success: bool
    type: Optional[str]
    filename: Optional[str]
    mime_type: Optional[str]
    size: Optional[int]
    data_uri: Optional[str]
    text_content: Optional[str]
    prompt: Optional[str]
    error: Optional[str]


class MultimodalContextResponse(BaseModel):
    has_images: bool
    has_documents: bool
    image_count: int
    document_count: int
    files: List[dict]
    total_size: int


@router.post("/upload", response_model=MultimodalUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    business_id: int = 0,
    session_id: str = "",
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and process a file (image or document).
    
    Args:
        file: Uploaded file
        business_id: Business ID
        session_id: Session ID
        current_user: Authenticated user
    
    Returns:
        Processing result
    """
    result = await multimodal_service.process_file(file, business_id, session_id)
    return result


@router.post("/upload-multiple", response_model=List[MultimodalUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    business_id: int = 0,
    session_id: str = "",
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and process multiple files.
    
    Args:
        files: List of uploaded files
        business_id: Business ID
        session_id: Session ID
        current_user: Authenticated user
    
    Returns:
        List of processing results
    """
    results = []
    for file in files:
        result = await multimodal_service.process_file(file, business_id, session_id)
        results.append(result)
    return results


@router.post("/context", response_model=MultimodalContextResponse)
def create_multimodal_context(
    processed_files: List[dict],
    current_user: User = Depends(get_current_active_user)
):
    """
    Create multimodal context from processed files.
    
    Args:
        processed_files: List of processed file results
        current_user: Authenticated user
    
    Returns:
        Multimodal context
    """
    context = multimodal_service.create_multimodal_context(processed_files)
    return context


@router.post("/prompt")
def generate_multimodal_prompt(
    user_message: str,
    processed_files: List[dict],
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate enhanced prompt including multimodal context.
    
    Args:
        user_message: Original user message
        processed_files: List of processed file results
        current_user: Authenticated user
    
    Returns:
        Enhanced prompt
    """
    context = multimodal_service.create_multimodal_context(processed_files)
    prompt = multimodal_service.generate_multimodal_prompt(
        user_message,
        context,
        processed_files
    )
    return {
        "prompt": prompt,
        "context": context
    }


@router.get("/supported-types")
def get_supported_types(current_user: User = Depends(get_current_active_user)):
    """
    Get list of supported file types.
    
    Args:
        current_user: Authenticated user
    
    Returns:
        Supported file types
    """
    return {
        "images": list(multimodal_service.SUPPORTED_IMAGE_TYPES),
        "documents": list(multimodal_service.SUPPORTED_DOCUMENT_TYPES),
        "max_file_size": multimodal_service.MAX_FILE_SIZE,
        "max_file_size_mb": multimodal_service.MAX_FILE_SIZE / (1024 * 1024)
    }