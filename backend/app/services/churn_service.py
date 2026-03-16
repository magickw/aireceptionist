"""
Customer Churn Prediction Service
Delegates to CustomerIntelligenceService as the single source of truth for churn scoring.
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func


class ChurnService:
    """Service for predicting customer churn risk."""

    def calculate_churn_risk(
        self,
        db: Session,
        customer_phone: str,
        business_id: int
    ) -> Dict:
        """
        Calculate churn risk for a customer.
        Delegates to CustomerIntelligenceService for consistent scoring.
        """
        import asyncio
        from app.services.customer_intelligence import customer_intelligence_service

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        customer_intelligence_service.calculate_churn_risk(customer_phone, business_id, db)
                    )
                    result = future.result(timeout=30)
            else:
                result = loop.run_until_complete(
                    customer_intelligence_service.calculate_churn_risk(customer_phone, business_id, db)
                )
        except Exception as e:
            print(f"[ChurnService] Error: {e}")
            result = {"churn_risk_score": 0.5, "risk_level": "unknown", "factors": {}}

        # Normalize to legacy format expected by callers
        score_0_100 = int(result.get("churn_risk_score", 0.5) * 100)
        return {
            "customer_phone": customer_phone,
            "risk_score": score_0_100,
            "risk_level": result.get("risk_level", "unknown"),
            "factors": result.get("factors", {}),
            "recommendations": result.get("recommendations", []),
        }

    def get_at_risk_customers(
        self,
        db: Session,
        business_id: int,
        min_risk_score: int = 40
    ) -> List[Dict]:
        """Get all customers with churn risk above threshold."""
        from app.models.models import CallSession

        customers = db.query(
            CallSession.customer_phone,
            func.max(CallSession.started_at).label('last_call')
        ).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone.isnot(None)
        ).group_by(
            CallSession.customer_phone
        ).all()

        at_risk = []
        for customer in customers:
            risk = self.calculate_churn_risk(db, customer.customer_phone, business_id)
            if risk["risk_score"] >= min_risk_score:
                at_risk.append(risk)

        at_risk.sort(key=lambda x: x["risk_score"], reverse=True)
        return at_risk

    def get_churn_stats(self, db: Session, business_id: int) -> Dict:
        """Get overall churn statistics."""
        at_risk = self.get_at_risk_customers(db, business_id, min_risk_score=40)

        high_risk = sum(1 for c in at_risk if c["risk_level"] == "high")
        medium_risk = sum(1 for c in at_risk if c["risk_level"] == "medium")
        low_risk = sum(1 for c in at_risk if c["risk_level"] == "low")
        total = len(at_risk)

        return {
            "total_at_risk": total,
            "distribution": {"high": high_risk, "medium": medium_risk, "low": low_risk},
            "percentages": {
                "high": round(high_risk / max(total, 1) * 100, 1),
                "medium": round(medium_risk / max(total, 1) * 100, 1),
                "low": round(low_risk / max(total, 1) * 100, 1),
            },
        }


churn_service = ChurnService()
