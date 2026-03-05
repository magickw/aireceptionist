"""
Customer Memory Service
DB-backed persistent memory for customer preferences, facts, and call summaries.
Enables the AI receptionist to recall past interactions and personalize conversations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
import boto3
import json
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("customer_memory")


class CustomerMemoryService:
    """
    Manages persistent customer memories across sessions.

    Memories are keyed by (customer_id, key) and categorized by memory_type
    (e.g. 'preference', 'fact', 'interaction', 'note'). Each memory tracks
    a confidence score, access count, and the session that produced it.
    """

    # ------------------------------------------------------------------ #
    # save_memory - upsert a single memory row
    # ------------------------------------------------------------------ #
    def save_memory(
        self,
        db: Session,
        customer_id: int,
        business_id: int,
        memory_type: str,
        key: str,
        value: str,
        confidence: float = 1.0,
        source_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upsert a customer memory keyed by (customer_id, key).

        If a memory with the same customer_id + key already exists, the value,
        confidence, source, and timestamp are updated. Otherwise a new row is
        created.

        Returns a dict representation of the saved memory.
        """
        from app.models.models import CustomerMemory

        try:
            existing = db.query(CustomerMemory).filter(
                and_(
                    CustomerMemory.customer_id == customer_id,
                    CustomerMemory.key == key,
                )
            ).first()

            if existing:
                existing.value = value
                existing.memory_type = memory_type
                existing.confidence = confidence
                existing.source_session_id = source_session_id
                existing.business_id = business_id
                existing.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing)
                logger.info(
                    "Updated memory customer_id=%s key=%s", customer_id, key
                )
                return self._memory_to_dict(existing)

            memory = CustomerMemory(
                customer_id=customer_id,
                business_id=business_id,
                memory_type=memory_type,
                key=key,
                value=value,
                confidence=confidence,
                source_session_id=source_session_id,
                access_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(memory)
            db.commit()
            db.refresh(memory)
            logger.info(
                "Created memory customer_id=%s key=%s type=%s",
                customer_id,
                key,
                memory_type,
            )
            return self._memory_to_dict(memory)

        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to save memory customer_id=%s key=%s: %s",
                customer_id,
                key,
                exc,
            )
            raise

    # ------------------------------------------------------------------ #
    # get_memories - retrieve memories with access tracking
    # ------------------------------------------------------------------ #
    def get_memories(
        self,
        db: Session,
        customer_id: int,
        business_id: int,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customer memories, optionally filtered by memory_type.

        Each returned memory has its access_count incremented so that we can
        track which memories are being actively used.
        """
        from app.models.models import CustomerMemory

        try:
            query = db.query(CustomerMemory).filter(
                and_(
                    CustomerMemory.customer_id == customer_id,
                    CustomerMemory.business_id == business_id,
                )
            )

            if memory_type is not None:
                query = query.filter(CustomerMemory.memory_type == memory_type)

            memories = (
                query.order_by(CustomerMemory.updated_at.desc())
                .limit(limit)
                .all()
            )

            # Increment access_count for every returned memory
            for mem in memories:
                mem.access_count = (mem.access_count or 0) + 1

            db.commit()

            return [self._memory_to_dict(m) for m in memories]

        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to get memories customer_id=%s: %s", customer_id, exc
            )
            return []

    # ------------------------------------------------------------------ #
    # build_memory_briefing - natural-language summary of stored memories
    # ------------------------------------------------------------------ #
    def build_memory_briefing(
        self,
        db: Session,
        customer_id: int,
        business_id: int,
    ) -> str:
        """
        Build a natural-language briefing from all stored memories for a
        customer.  The briefing is intended to be injected into the AI
        system prompt so the receptionist can personalize the conversation.

        Format:
            ## Customer Memory Briefing
            - [preference] Preferred appointment time: mornings
            - [fact] Has 2 dogs (mentioned 2023-05-01)
            - Last call summary: Booked grooming appointment, was satisfied
        """
        from app.models.models import CustomerMemory, CallSummaryV2

        try:
            memories = (
                db.query(CustomerMemory)
                .filter(
                    and_(
                        CustomerMemory.customer_id == customer_id,
                        CustomerMemory.business_id == business_id,
                    )
                )
                .order_by(CustomerMemory.updated_at.desc())
                .limit(30)
                .all()
            )

            if not memories:
                # Check for a call summary even when no discrete memories exist
                last_summary = (
                    db.query(CallSummaryV2)
                    .filter(
                        and_(
                            CallSummaryV2.customer_id == customer_id,
                            CallSummaryV2.business_id == business_id,
                        )
                    )
                    .order_by(CallSummaryV2.created_at.desc())
                    .first()
                )
                if last_summary and last_summary.summary:
                    return (
                        "## Customer Memory Briefing\n"
                        f"- Last call summary: {last_summary.summary}"
                    )
                return ""

            lines = ["## Customer Memory Briefing"]

            for mem in memories:
                mem_type = mem.memory_type or "info"
                date_str = ""
                if mem.created_at:
                    date_str = f" (mentioned {mem.created_at.strftime('%Y-%m-%d')})"

                if mem_type == "preference":
                    lines.append(f"- [preference] {mem.key}: {mem.value}")
                elif mem_type == "fact":
                    lines.append(f"- [fact] {mem.value}{date_str}")
                elif mem_type == "interaction":
                    lines.append(f"- [interaction] {mem.key}: {mem.value}")
                elif mem_type == "note":
                    lines.append(f"- [note] {mem.value}")
                else:
                    lines.append(f"- [{mem_type}] {mem.key}: {mem.value}")

            # Append the most recent call summary if available
            last_summary = (
                db.query(CallSummaryV2)
                .filter(
                    and_(
                        CallSummaryV2.customer_id == customer_id,
                        CallSummaryV2.business_id == business_id,
                    )
                )
                .order_by(CallSummaryV2.created_at.desc())
                .first()
            )
            if last_summary and last_summary.summary:
                lines.append(f"- Last call summary: {last_summary.summary}")

            return "\n".join(lines)

        except Exception as exc:
            logger.error(
                "Failed to build memory briefing customer_id=%s: %s",
                customer_id,
                exc,
            )
            return ""

    # ------------------------------------------------------------------ #
    # summarize_call - LLM-powered call summarization
    # ------------------------------------------------------------------ #
    def summarize_call(
        self,
        db: Session,
        call_session_id: str,
        customer_id: int,
        business_id: int,
        conversation_messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Summarize a completed call using Amazon Nova Lite via the Bedrock
        converse API.

        The model produces structured JSON with:
          - summary: concise paragraph
          - key_topics: list of discussed topics
          - outcome: what was resolved / decided
          - action_items: list of follow-up actions
          - extracted_facts: dict of facts learned about the customer
          - sentiment_arc: e.g. "neutral->positive"

        The result is persisted in the ``call_summaries_v2`` table and any
        extracted facts are saved as individual customer memories.
        """
        from app.models.models import CallSummaryV2

        if not conversation_messages:
            logger.warning(
                "summarize_call called with empty messages for session=%s",
                call_session_id,
            )
            return {}

        # -- Build the transcript text -------------------------------- #
        transcript_lines = []
        for msg in conversation_messages:
            role = msg.get("sender", msg.get("role", "unknown"))
            content = msg.get("content", msg.get("text", ""))
            transcript_lines.append(f"{role}: {content}")
        transcript = "\n".join(transcript_lines)

        # -- Build the prompt ----------------------------------------- #
        prompt = (
            "You are an expert call analyst. Analyze the following phone call "
            "transcript between a customer and an AI receptionist. Produce a "
            "JSON object with exactly these keys:\n"
            "- \"summary\": a concise 1-3 sentence summary of the call\n"
            "- \"key_topics\": a JSON array of the main topics discussed\n"
            "- \"outcome\": what was resolved or decided during the call\n"
            "- \"action_items\": a JSON array of any follow-up actions needed\n"
            "- \"extracted_facts\": a JSON object of facts learned about the "
            "customer (e.g. {\"preferred_time\": \"mornings\", \"pet_count\": \"2 dogs\"})\n"
            "- \"sentiment_arc\": a short string describing how sentiment "
            "changed during the call (e.g. \"neutral->positive\", "
            "\"frustrated->satisfied\")\n\n"
            "Return ONLY the JSON object. No markdown fences, no explanation.\n\n"
            f"TRANSCRIPT:\n{transcript}"
        )

        # -- Call Bedrock Nova Lite ----------------------------------- #
        try:
            client = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            response = client.converse(
                modelId="amazon.nova-lite-v1:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 512, "temperature": 0.3},
            )

            raw_text = (
                response.get("output", {})
                .get("message", {})
                .get("content", [{}])[0]
                .get("text", "{}")
            )

            # Strip markdown code fences if the model wraps them anyway
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

            summary_data = json.loads(cleaned)

        except json.JSONDecodeError as jde:
            logger.error(
                "Failed to parse summarization JSON for session=%s: %s raw=%s",
                call_session_id,
                jde,
                raw_text if "raw_text" in dir() else "N/A",
            )
            summary_data = {
                "summary": raw_text if "raw_text" in dir() else "",
                "key_topics": [],
                "outcome": "",
                "action_items": [],
                "extracted_facts": {},
                "sentiment_arc": "unknown",
            }
        except Exception as exc:
            logger.error(
                "Bedrock converse call failed for session=%s: %s",
                call_session_id,
                exc,
            )
            summary_data = {
                "summary": "",
                "key_topics": [],
                "outcome": "",
                "action_items": [],
                "extracted_facts": {},
                "sentiment_arc": "unknown",
            }

        # -- Persist to call_summaries_v2 ----------------------------- #
        try:
            call_summary = CallSummaryV2(
                call_session_id=call_session_id,
                customer_id=customer_id,
                business_id=business_id,
                summary=summary_data.get("summary", ""),
                key_topics=summary_data.get("key_topics", []),
                outcome=summary_data.get("outcome", ""),
                action_items=summary_data.get("action_items", []),
                extracted_facts=summary_data.get("extracted_facts", {}),
                sentiment_arc=summary_data.get("sentiment_arc", ""),
                created_at=datetime.now(timezone.utc),
            )
            db.add(call_summary)
            db.commit()
            db.refresh(call_summary)
            logger.info(
                "Saved call summary id=%s for session=%s",
                call_summary.id,
                call_session_id,
            )
        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to persist call summary for session=%s: %s",
                call_session_id,
                exc,
            )

        # -- Extract memories from the summary ------------------------ #
        extracted_facts = summary_data.get("extracted_facts", {})
        if isinstance(extracted_facts, dict):
            for fact_key, fact_value in extracted_facts.items():
                try:
                    self.save_memory(
                        db=db,
                        customer_id=customer_id,
                        business_id=business_id,
                        memory_type="fact",
                        key=fact_key,
                        value=str(fact_value),
                        confidence=0.85,
                        source_session_id=call_session_id,
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to save extracted fact key=%s: %s",
                        fact_key,
                        exc,
                    )

        return summary_data

    # ------------------------------------------------------------------ #
    # flush_session_memories - batch-save in-memory session data to DB
    # ------------------------------------------------------------------ #
    def flush_session_memories(
        self,
        db: Session,
        session_memories: Dict[str, Any],
        customer_id: int,
        business_id: int,
        source_session_id: Optional[str] = None,
    ) -> int:
        """
        Persist a batch of in-memory session memories to the database.

        ``session_memories`` is expected to be a dict where each key maps to
        a dict with at least ``value`` and optionally ``memory_type`` and
        ``confidence``.

        Example::

            {
                "preferred_time": {"value": "mornings", "memory_type": "preference", "confidence": 0.95},
                "pet_count": {"value": "2 dogs", "memory_type": "fact"},
            }

        Returns the number of memories successfully saved.
        """
        saved_count = 0

        if not session_memories or not isinstance(session_memories, dict):
            return saved_count

        for key, payload in session_memories.items():
            if not isinstance(payload, dict):
                # Accept simple string values as well
                payload = {"value": str(payload)}

            value = payload.get("value", "")
            if not value:
                continue

            memory_type = payload.get("memory_type", "fact")
            confidence = payload.get("confidence", 1.0)

            try:
                self.save_memory(
                    db=db,
                    customer_id=customer_id,
                    business_id=business_id,
                    memory_type=memory_type,
                    key=key,
                    value=str(value),
                    confidence=confidence,
                    source_session_id=source_session_id,
                )
                saved_count += 1
            except Exception as exc:
                logger.error(
                    "flush_session_memories failed for key=%s: %s", key, exc
                )

        logger.info(
            "Flushed %d/%d session memories for customer_id=%s session=%s",
            saved_count,
            len(session_memories),
            customer_id,
            source_session_id,
        )
        return saved_count

    # ------------------------------------------------------------------ #
    # recall_customer_memory - tool handler for recallCustomerMemory
    # ------------------------------------------------------------------ #
    def recall_customer_memory(
        self,
        db: Session,
        customer_id: int,
        business_id: int,
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Tool handler for the ``recallCustomerMemory`` tool.

        Searches customer memories by case-insensitive keyword match on both
        the key and value columns. Returns matching memories ordered by
        relevance (updated_at descending).
        """
        from app.models.models import CustomerMemory

        if not query or not query.strip():
            return []

        search_term = f"%{query.strip().lower()}%"

        try:
            from sqlalchemy import func as sa_func

            memories = (
                db.query(CustomerMemory)
                .filter(
                    and_(
                        CustomerMemory.customer_id == customer_id,
                        CustomerMemory.business_id == business_id,
                    )
                )
                .filter(
                    sa_func.lower(CustomerMemory.key).like(search_term)
                    | sa_func.lower(CustomerMemory.value).like(search_term)
                )
                .order_by(CustomerMemory.updated_at.desc())
                .limit(10)
                .all()
            )

            # Increment access counts
            for mem in memories:
                mem.access_count = (mem.access_count or 0) + 1
            db.commit()

            results = [self._memory_to_dict(m) for m in memories]
            logger.info(
                "recall_customer_memory query=%s customer_id=%s found=%d",
                query,
                customer_id,
                len(results),
            )
            return results

        except Exception as exc:
            db.rollback()
            logger.error(
                "recall_customer_memory failed customer_id=%s query=%s: %s",
                customer_id,
                query,
                exc,
            )
            return []

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _memory_to_dict(memory) -> Dict[str, Any]:
        """Convert a CustomerMemory ORM instance to a plain dict."""
        return {
            "id": memory.id,
            "customer_id": memory.customer_id,
            "business_id": memory.business_id,
            "memory_type": memory.memory_type,
            "key": memory.key,
            "value": memory.value,
            "confidence": float(memory.confidence) if memory.confidence is not None else 1.0,
            "access_count": memory.access_count or 0,
            "source_session_id": memory.source_session_id,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
        }


# Module-level singleton
customer_memory_service = CustomerMemoryService()
