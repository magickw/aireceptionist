"""
Knowledge Base RAG Service using Nova Multimodal Embeddings + pgvector

This service provides:
- Document upload and text chunking
- Vector embedding generation using Nova Embeddings
- Semantic search across knowledge base
- Business-specific knowledge retrieval
"""

import boto3
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import numpy as np

from app.core.config import settings
from app.models.models import KnowledgeBaseDocument, DocumentChunk, Business


class KnowledgeBaseService:
    """
    Knowledge Base RAG service using Nova Embeddings and pgvector
    """
    
    # Titan Text Embedding dimension is 1536
    EMBEDDING_DIMENSION = 1536
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        # Use stable Titan Embeddings model as fallback for Nova
        self.embedding_model_id = "amazon.titan-embed-text-v1"
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation.
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List of text chunks
        """
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('\n', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(text) else len(text)
        
        return chunks
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Nova Embeddings.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        body = {
            "inputText": text[:10000]  # Limit input size
        }
        
        if not body["inputText"].strip():
            return []
        response = self.bedrock_runtime.invoke_model(
            modelId=self.embedding_model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response["body"].read().decode())
        
        # Extract embedding from response
        if "embedding" in response_body:
            return response_body["embedding"]
        else:
            raise ValueError(f"Unexpected embedding response format: {response_body}")
    
    async def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Process in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)
        
        async def embed_with_limit(text: str):
            async with semaphore:
                return await self._get_embedding(text)
        
        tasks = [embed_with_limit(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def process_document(
        self,
        document_id: int,
        content: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process a document: chunk text and create embeddings.
        
        Args:
            document_id: ID of the document in database
            content: Text content to process
            db: Database session
            
        Returns:
            Processing result with chunk count
        """
        try:
            # Update document status
            document = db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.id == document_id
            ).first()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            document.status = "indexing"
            db.commit()
            
            # Chunk the text
            chunks = self._chunk_text(content)
            
            # Generate embeddings in batch
            embeddings = await self._get_embeddings_batch(chunks)
            
            # Store chunks with embeddings
            for chunk_text, embedding in zip(chunks, embeddings):
                chunk = DocumentChunk(
                    document_id=document_id,
                    content=chunk_text,
                    embedding=embedding
                )
                db.add(chunk)
            
            # Update document status
            document.status = "complete"
            document.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "success": True,
                "document_id": document_id,
                "chunks_created": len(chunks)
            }
            
        except Exception as e:
            # Update document status on error
            if document:
                document.status = "failed"
                document.error_message = str(e)
                db.commit()
            
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }
    
    async def search(
        self,
        query: str,
        business_id: int,
        db: Session,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across knowledge base for a business.
        
        Args:
            query: Search query
            business_id: Business ID to search within
            db: Database session
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await self._get_embedding(query)
            
            # Search using pgvector cosine similarity
            # Using raw SQL for pgvector similarity search
            from sqlalchemy import text
            
            # Convert embedding to postgres array format
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Execute similarity search
            # Use CAST() instead of :: for type casting with named parameters
            result = db.execute(
                text("""
                    SELECT 
                        dc.id,
                        dc.content,
                        dc.document_id,
                        kbd.file_name,
                        -- Cosine similarity (1 - cosine_distance)
                        (1 - (dc.embedding <=> CAST(:embedding AS vector))) as similarity
                    FROM document_chunks dc
                    JOIN knowledge_base_documents kbd ON dc.document_id = kbd.id
                    WHERE kbd.business_id = :business_id
                    AND kbd.status = 'complete'
                    ORDER BY dc.embedding <=> CAST(:embedding AS vector)
                    LIMIT :top_k
                """),
                {
                    "embedding": embedding_str,
                    "business_id": business_id,
                    "top_k": top_k
                }
            )
            
            search_results = []
            for row in result:
                search_results.append({
                    "chunk_id": row[0],
                    "content": row[1],
                    "document_id": row[2],
                    "file_name": row[3],
                    "similarity": float(row[4])
                })
            
            return search_results
            
        except Exception as e:
            print(f"Error in knowledge base search: {e}")
            return []
    
    async def get_relevant_context(
        self,
        query: str,
        business_id: int,
        db: Session,
        max_chars: int = 2000
    ) -> str:
        if not query or not query.strip():
            return ""
        results = await self.search(query, business_id, db, top_k=5)
        
        if not results:
            return ""
        
        context_parts = []
        current_chars = 0
        
        for result in results:
            if current_chars + len(result["content"]) > max_chars:
                break
            context_parts.append(f"[From {result['file_name']}]: {result['content']}")
            current_chars += len(result["content"])
        
        return "\n\n".join(context_parts)
    
    async def create_document(
        self,
        business_id: int,
        file_name: str,
        file_type: str,
        content: str,
        db: Session
    ) -> KnowledgeBaseDocument:
        """
        Create a new knowledge base document and process it.
        
        Args:
            business_id: Business ID
            file_name: Name of the file
            file_type: Type of file (txt, md, pdf, etc.)
            content: Text content of the document
            db: Database session
            
        Returns:
            Created document
        """
        # Create document record
        document = KnowledgeBaseDocument(
            business_id=business_id,
            file_name=file_name,
            file_type=file_type,
            status="pending"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document asynchronously
        await self.process_document(document.id, content, db)
        
        return document
    
    def list_documents(
        self,
        business_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> List[KnowledgeBaseDocument]:
        """
        List all documents for a business.
        """
        return db.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.business_id == business_id
        ).order_by(desc(KnowledgeBaseDocument.created_at)).offset(skip).limit(limit).all()
    
    def get_document(
        self,
        document_id: int,
        business_id: int,
        db: Session
    ) -> Optional[KnowledgeBaseDocument]:
        """Get a specific document."""
        return db.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.id == document_id,
            KnowledgeBaseDocument.business_id == business_id
        ).first()
    
    def delete_document(
        self,
        document_id: int,
        business_id: int,
        db: Session
    ) -> bool:
        """Delete a document and its chunks."""
        document = self.get_document(document_id, business_id, db)
        if not document:
            return False
        
        # Delete chunks (cascade should handle this)
        db.delete(document)
        db.commit()
        return True


# Singleton instance
knowledge_base_service = KnowledgeBaseService()
