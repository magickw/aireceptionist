"""Multimodal Service - Support for image and document processing"""

import base64
import mimetypes
from typing import Optional, Dict, Any, List
from fastapi import UploadFile
import io


class MultimodalService:
    """
    Service for handling multimodal inputs (images, documents).
    Supports file upload, validation, and processing for AI reasoning.
    """
    
    # Supported file types
    SUPPORTED_IMAGE_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'
    }
    
    SUPPORTED_DOCUMENT_TYPES = {
        'application/pdf', 'text/plain', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self.supported_types = self.SUPPORTED_IMAGE_TYPES.union(self.SUPPORTED_DOCUMENT_TYPES)
    
    async def process_file(
        self,
        file: UploadFile,
        business_id: int,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process an uploaded file (image or document).
        
        Args:
            file: Uploaded file
            business_id: Business ID
            session_id: Session ID
        
        Returns:
            Processing result with file info and extracted content
        """
        # Validate file
        validation_result = self.validate_file(file)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["error"]
            }
        
        # Read file content
        content = await file.read()
        
        # Determine file type
        file_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        # Process based on type
        if file_type in self.SUPPORTED_IMAGE_TYPES:
            return await self._process_image(content, file.filename, file_type, business_id, session_id)
        elif file_type in self.SUPPORTED_DOCUMENT_TYPES:
            return await self._process_document(content, file.filename, file_type, business_id, session_id)
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_type}"
            }
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file
        
        Returns:
            Validation result
        """
        # Check file size
        if file.size and file.size > self.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"File size exceeds maximum of {self.MAX_FILE_SIZE / (1024*1024)}MB"
            }
        
        # Check file type
        file_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        if file_type not in self.supported_types:
            return {
                "valid": False,
                "error": f"Unsupported file type: {file_type}. Supported types: {', '.join(self.supported_types)}"
            }
        
        return {"valid": True}
    
    async def _process_image(
        self,
        content: bytes,
        filename: str,
        file_type: str,
        business_id: int,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process image file.
        
        Args:
            content: File content
            filename: File name
            file_type: MIME type
            business_id: Business ID
            session_id: Session ID
        
        Returns:
            Processing result
        """
        # Convert to base64 for API transmission
        base64_content = base64.b64encode(content).decode('utf-8')
        data_uri = f"data:{file_type};base64,{base64_content}"
        
        # Generate image analysis prompt
        prompt = self._generate_image_analysis_prompt(filename)
        
        return {
            "success": True,
            "type": "image",
            "filename": filename,
            "mime_type": file_type,
            "size": len(content),
            "data_uri": data_uri,
            "prompt": prompt,
            "session_id": session_id,
            "business_id": business_id
        }
    
    async def _process_document(
        self,
        content: bytes,
        filename: str,
        file_type: str,
        business_id: int,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process document file.
        
        Args:
            content: File content
            filename: File name
            file_type: MIME type
            business_id: Business ID
            session_id: Session ID
        
        Returns:
            Processing result
        """
        # Extract text from document
        text_content = self._extract_text_from_document(content, file_type)
        
        return {
            "success": True,
            "type": "document",
            "filename": filename,
            "mime_type": file_type,
            "size": len(content),
            "text_content": text_content,
            "text_length": len(text_content),
            "session_id": session_id,
            "business_id": business_id
        }
    
    def _generate_image_analysis_prompt(self, filename: str) -> str:
        """Generate prompt for image analysis"""
        return f"""You are a business assistant analyzing an image from a customer. 

The customer has uploaded an image file: {filename}

Please analyze this image and provide:
1. A description of what's in the image
2. Any relevant business context (e.g., if it's a menu item, product, document, etc.)
3. What action might be needed based on this image
4. Any specific information you can extract

Focus on details that would be relevant for a business receptionist AI assistant."""
    
    def _extract_text_from_document(self, content: bytes, file_type: str) -> str:
        """
        Extract text from document.
        """
        if file_type == 'text/plain':
            return content.decode('utf-8', errors='ignore')
        elif file_type == 'application/pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content))
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(io.BytesIO(content))
                    return "\n".join(page.extract_text() or "" for page in reader.pages)
                except ImportError:
                    return "[PDF extraction requires pypdf: pip install pypdf]"
        elif file_type in ['application/msword',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            try:
                import docx
                doc = docx.Document(io.BytesIO(content))
                return "\n".join(para.text for para in doc.paragraphs)
            except ImportError:
                return "[Word extraction requires python-docx: pip install python-docx]"
        return "[Unable to extract text from this document type]"
    
    def create_multimodal_context(
        self,
        processed_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multimodal context for AI reasoning.
        
        Args:
            processed_files: List of processed file results
        
        Returns:
            Multimodal context dictionary
        """
        context = {
            "has_images": False,
            "has_documents": False,
            "image_count": 0,
            "document_count": 0,
            "files": [],
            "total_size": 0
        }
        
        for file_data in processed_files:
            if not file_data.get("success"):
                continue
            
            context["files"].append({
                "type": file_data["type"],
                "filename": file_data["filename"],
                "mime_type": file_data["mime_type"],
                "size": file_data["size"]
            })
            
            context["total_size"] += file_data["size"]
            
            if file_data["type"] == "image":
                context["has_images"] = True
                context["image_count"] += 1
            elif file_data["type"] == "document":
                context["has_documents"] = True
                context["document_count"] += 1
        
        return context
    
    def generate_multimodal_prompt(
        self,
        user_message: str,
        multimodal_context: Dict[str, Any],
        processed_files: List[Dict[str, Any]]
    ) -> str:
        """
        Generate enhanced prompt including multimodal context.
        
        Args:
            user_message: Original user message
            multimodal_context: Multimodal context
            processed_files: List of processed file results
        
        Returns:
            Enhanced prompt
        """
        prompt = f"Customer Message: {user_message}\n\n"
        
        if multimodal_context["has_images"]:
            prompt += f"Customer has uploaded {multimodal_context['image_count']} image(s).\n"
        
        if multimodal_context["has_documents"]:
            prompt += f"Customer has uploaded {multimodal_context['document_count']} document(s).\n"
        
        # Add content from processed files
        for file_data in processed_files:
            if not file_data.get("success"):
                continue
            
            if file_data["type"] == "image":
                prompt += f"\nImage Analysis for {file_data['filename']}:\n"
                prompt += f"{file_data.get('prompt', 'Analyze the uploaded image.')}\n"
            elif file_data["type"] == "document":
                prompt += f"\nDocument Content from {file_data['filename']}:\n"
                text_content = file_data.get("text_content", "")
                # Truncate very long documents
                if len(text_content) > 2000:
                    text_content = text_content[:2000] + "... [truncated]"
                prompt += f"{text_content}\n"
        
        prompt += "\nPlease consider all provided information when formulating your response."
        
        return prompt


# Singleton instance
multimodal_service = MultimodalService()


def process_uploaded_file(file: UploadFile, business_id: int, session_id: str) -> Dict[str, Any]:
    """Convenience function for processing uploaded files (sync wrapper)."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Already inside an async context — callers should use await directly
        raise RuntimeError(
            "process_uploaded_file() cannot be called from an async context. "
            "Use 'await multimodal_service.process_file(...)' instead."
        )
    return asyncio.run(multimodal_service.process_file(file, business_id, session_id))
