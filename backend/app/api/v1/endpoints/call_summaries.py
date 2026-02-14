"""
Call Summaries API Endpoint

Provides endpoints for:
- Generating post-call summaries using Nova 2 Lite
- Extracting key information from call transcripts
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import boto3
import json

from app.api import deps
from app.core.config import settings


router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class SummaryRequest(BaseModel):
    messages: List[Message]
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    business_id: Optional[int] = None


class CallSummary(BaseModel):
    summary: str
    sentiment: str
    key_points: List[str]
    action_items: List[str]
    customer_intent: str
    next_steps: Optional[List[str]] = None


def generate_summary_with_nova(messages: List[Dict[str, str]]) -> CallSummary:
    """
    Generate a call summary using Nova 2 Lite.
    
    Args:
        messages: List of message objects with role and content
        
    Returns:
        Structured summary with key information
    """
    # Initialize Bedrock client
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
    # Format conversation for the prompt
    conversation = "\n".join([
        f"{msg['role'].capitalize()}: {msg['content']}"
        for msg in messages
    ])
    
    system_prompt = """You are a professional call summary assistant. Your task is to analyze customer service call transcripts and generate structured summaries.

Analyze the conversation and provide a JSON response with the following structure:
{
  "summary": "One sentence summary of the call",
  "sentiment": "positive, neutral, or negative",
  "key_points": ["List of important points from the call"],
  "action_items": ["Any actions that need to be taken"],
  "customer_intent": "The main reason for the customer's call",
  "next_steps": ["Recommended follow-up actions"]
}

Be concise and professional. Extract only the most important information."""

    user_message = f"Please summarize this call transcript:\n\n{conversation}"

    body = {
        "messages": [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "system": [{"text": system_prompt}],
        "inferenceConfig": {
            "maxTokens": 1024,
            "temperature": 0.1,
            "topP": 0.9
        }
    }
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId="amazon.nova-lite-v1:0",
            body=json.dumps(body)
        )
        
        response_body = json.loads(response["body"].read().decode())
        
        # Extract the content from the response
        if "messages" in response_body and len(response_body["messages"]) > 0:
            content = response_body["messages"][0]["content"]
            
            # Try to parse JSON from the response
            try:
                # Find JSON in the response
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    summary_data = json.loads(json_match.group())
                else:
                    summary_data = json.loads(content)
                
                return CallSummary(
                    summary=summary_data.get("summary", "Call completed"),
                    sentiment=summary_data.get("sentiment", "neutral"),
                    key_points=summary_data.get("key_points", []),
                    action_items=summary_data.get("action_items", []),
                    customer_intent=summary_data.get("customer_intent", "Unknown"),
                    next_steps=summary_data.get("next_steps", [])
                )
            except json.JSONDecodeError:
                # If JSON parsing fails, create a basic summary
                return CallSummary(
                    summary=content[:200] if len(content) > 200 else content,
                    sentiment="neutral",
                    key_points=[],
                    action_items=[],
                    customer_intent="Unknown"
                )
        else:
            raise ValueError("Unexpected response format")
            
    except Exception as e:
        print(f"Error generating summary: {e}")
        # Return a fallback summary
        return CallSummary(
            summary="Call completed. Summary generation failed.",
            sentiment="neutral",
            key_points=["Call processed"],
            action_items=[],
            customer_intent="Unknown"
        )


@router.post("/summarize")
async def summarize_call(
    request: SummaryRequest,
    business_id: int = Depends(deps.get_current_business_id)
):
    """
    Generate a post-call summary from a conversation transcript.
    
    Takes a list of messages and returns a structured summary including:
    - One-sentence summary
    - Detected sentiment
    - Key points
    - Action items
    - Customer intent
    - Recommended next steps
    """
    try:
        # Convert messages to the format expected by the function
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # Generate summary
        summary = generate_summary_with_nova(messages)
        
        return {
            "success": True,
            "summary": summary.dict(),
            "metadata": {
                "customer_phone": request.customer_phone,
                "customer_name": request.customer_name,
                "message_count": len(messages)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{call_session_id}")
async def get_call_summary(
    call_session_id: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Get an existing call summary from the database.
    
    If a summary was previously generated and stored, retrieve it.
    Otherwise, generate a new one from stored messages.
    """
    try:
        from app.models.models import CallSession, ConversationMessage
        
        # Get the call session
        call_session = db.query(CallSession).filter(
            CallSession.id == call_session_id,
            CallSession.business_id == business_id
        ).first()
        
        if not call_session:
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # If summary already exists, return it
        if call_session.summary:
            return {
                "success": True,
                "summary": json.loads(call_session.summary),
                "generated": True
            }
        
        # Get conversation messages
        messages = db.query(ConversationMessage).filter(
            ConversationMessage.call_session_id == call_session_id
        ).order_by(ConversationMessage.timestamp).all()
        
        if not messages:
            return {
                "success": False,
                "message": "No messages found for this call"
            }
        
        # Convert to format for summary generation
        msg_list = [
            {"role": msg.sender, "content": msg.content}
            for msg in messages
        ]
        
        # Generate summary
        summary = generate_summary_with_nova(msg_list)
        
        # Store the summary in the call session
        call_session.summary = json.dumps(summary.dict())
        db.commit()
        
        return {
            "success": True,
            "summary": summary.dict(),
            "generated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
