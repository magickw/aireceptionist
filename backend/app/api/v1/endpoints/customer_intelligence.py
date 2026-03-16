"""
Customer Intelligence API Endpoints

Provides endpoints for:
- Churn risk analysis
- VIP customer identification
- Semantic search across customer history
- Complaint pattern detection
- Customer list and details

Integrates with Customer 360 for richer customer profiles including:
- Lifetime value (LTV)
- Loyalty tiers
- AI-powered insights
- Personalized recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List

from app.api import deps
from app.services.customer_intelligence import customer_intelligence_service
from app.services.customer_360_service import customer_360_service
from app.models.models import CallSession, Appointment, Customer


router = APIRouter()


@router.get("/customers")
async def get_all_customers(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "last_contact",
    sort_order: str = "desc"
):
    """
    Get all customers for a business with pagination.
    
    Returns list of customers with their metrics including:
    - Call count
    - Appointment count
    - Average satisfaction
    - Last contact date
    - Churn risk (if calculable)
    - VIP status
    - Loyalty tier (from Customer 360)
    - Lifetime value (from Customer 360)
    """
    try:
        # Get customers from Customer 360 for richer data
        segments = await customer_360_service.get_customer_segments(db, business_id)
        
        # Get unique customer phones from call sessions
        offset = (page - 1) * page_size
        
        # Query for customer summary with Customer model join
        from sqlalchemy import func, cast, Float
        
        # Get Customer records with their data
        customer_records = db.query(Customer).filter(
            Customer.business_id == business_id
        ).all()
        
        # Build customer list from Customer model (Customer 360 data)
        customer_map = {}
        
        for c in customer_records:
            customer_map[c.phone] = {
                'phone': c.phone,
                'name': c.name,
                'email': c.email,
                'call_count': c.total_calls or 0,
                'last_contact': c.last_interaction.isoformat() if c.last_interaction else None,
                'avg_confidence': float(c.avg_quality_score) / 100 if c.avg_quality_score else 0.5,
                'appointment_count': c.total_appointments or 0,
                'churn_risk': {'risk_level': 'high' if float(c.churn_risk or 0) > 0.6 else 'medium' if float(c.churn_risk or 0) > 0.3 else 'low', 'risk_score': float(c.churn_risk or 0)} if c.churn_risk else None,
                'vip_status': {'tier': c.loyalty_tier, 'is_vip': c.is_vip} if c.is_vip or c.loyalty_tier else None,
                'loyalty_tier': c.loyalty_tier,
                'total_spent': float(c.total_spent) if c.total_spent else 0,
                'is_vip': c.is_vip
            }
        
        # Also get call session data for customers not in Customer table
        call_stats = db.query(
            CallSession.customer_phone,
            func.count(CallSession.id).label('call_count'),
            func.max(CallSession.started_at).label('last_contact'),
            func.avg(CallSession.ai_confidence).label('avg_confidence')
        ).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone.isnot(None)
        ).group_by(
            CallSession.customer_phone
        ).all()
        
        for r in call_stats:
            phone = r.customer_phone
            if phone not in customer_map:
                customer_map[phone] = {
                    'phone': phone,
                    'name': None,
                    'email': None,
                    'call_count': r.call_count or 0,
                    'last_contact': r.last_contact.isoformat() if r.last_contact else None,
                    'avg_confidence': float(r.avg_confidence) if r.avg_confidence else 0,
                    'appointment_count': 0,
                    'churn_risk': None,
                    'vip_status': None,
                    'loyalty_tier': 'standard',
                    'total_spent': 0,
                    'is_vip': False
                }
        
        # Get appointment counts
        appointment_stats = db.query(
            Appointment.customer_phone,
            func.count(Appointment.id).label('appointment_count')
        ).filter(
            Appointment.business_id == business_id,
            Appointment.customer_phone.isnot(None)
        ).group_by(
            Appointment.customer_phone
        ).all()
        
        for r in appointment_stats:
            phone = r.customer_phone
            if phone in customer_map:
                customer_map[phone]['appointment_count'] = r.appointment_count or 0
        
        # Convert to list
        customers = list(customer_map.values())
        
        # Sort
        if sort_by == 'last_contact':
            customers.sort(key=lambda x: x['last_contact'] or '', reverse=(sort_order == 'desc'))
        elif sort_by == 'call_count':
            customers.sort(key=lambda x: x['call_count'], reverse=(sort_order == 'desc'))
        elif sort_by == 'total_spent':
            customers.sort(key=lambda x: x.get('total_spent', 0), reverse=(sort_order == 'desc'))
        elif sort_by == 'loyalty_tier':
            tier_order = {'platinum': 4, 'gold': 3, 'silver': 2, 'standard': 1}
            customers.sort(key=lambda x: tier_order.get(x.get('loyalty_tier', 'standard'), 0), reverse=(sort_order == 'desc'))
        
        # Paginate
        total = len(customers)
        paginated_customers = customers[offset:offset + page_size]
        
        return {
            "customers": paginated_customers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "segments_summary": segments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{customer_phone}")
async def get_customer_details(
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Get detailed information about a specific customer.
    
    Includes Customer 360 data:
    - Churn risk analysis
    - VIP status and loyalty tier
    - Lifetime value (LTV)
    - AI-generated insights
    - Personalized recommendations
    - Recent calls and appointments
    """
    try:
        # Get Customer 360 profile for rich data
        profile_360 = await customer_360_service.get_customer_profile(db, business_id, customer_phone)
        
        # Get call sessions
        calls = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone == customer_phone
        ).order_by(desc(CallSession.started_at)).limit(10).all()
        
        # Get appointments
        appointments = db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.customer_phone == customer_phone
        ).order_by(desc(Appointment.appointment_time)).limit(10).all()
        
        # Use Customer 360 data if available, otherwise compute
        if "error" not in profile_360:
            return {
                "phone": customer_phone,
                "customer": profile_360.get("customer", {}),
                "metrics": profile_360.get("metrics", {}),
                "lifetime_value": profile_360.get("lifetime_value", {}),
                "recent_activity": profile_360.get("recent_activity", {
                    "calls": [
                        {
                            "id": c.id,
                            "started_at": c.started_at.isoformat() if c.started_at else None,
                            "duration_seconds": c.duration_seconds,
                            "ai_confidence": float(c.ai_confidence) if c.ai_confidence else None,
                            "sentiment": c.sentiment,
                            "quality_score": float(c.quality_score) if c.quality_score else None,
                            "summary": c.summary,
                            "status": c.status
                        }
                        for c in calls
                    ],
                    "orders": [],
                    "appointments": [
                        {
                            "id": a.id,
                            "customer_name": a.customer_name,
                            "appointment_time": a.appointment_time.isoformat() if a.appointment_time else None,
                            "service_type": a.service_type,
                            "status": a.status,
                            "notes": a.notes
                        }
                        for a in appointments
                    ]
                }),
                "insights": profile_360.get("insights", []),
                "recommendations": profile_360.get("recommendations", []),
                "calls": [
                    {
                        "id": c.id,
                        "started_at": c.started_at.isoformat() if c.started_at else None,
                        "duration_seconds": c.duration_seconds,
                        "ai_confidence": float(c.ai_confidence) if c.ai_confidence else None,
                        "sentiment": c.sentiment,
                        "quality_score": float(c.quality_score) if c.quality_score else None,
                        "summary": c.summary,
                        "status": c.status
                    }
                    for c in calls
                ],
                "appointments": [
                    {
                        "id": a.id,
                        "customer_name": a.customer_name,
                        "appointment_time": a.appointment_time.isoformat() if a.appointment_time else None,
                        "service_type": a.service_type,
                        "status": a.status,
                        "notes": a.notes
                    }
                    for a in appointments
                ],
                "stats": {
                    "total_calls": len(calls),
                    "total_appointments": len(appointments)
                }
            }
        
        # Fallback to basic computation
        churn_risk = await customer_intelligence_service.calculate_churn_risk(
            customer_phone=customer_phone,
            business_id=business_id,
            db=db
        )
        
        vip_customers = await customer_intelligence_service.identify_vip_customers(
            business_id=business_id,
            db=db
        )
        vip_status = next((c for c in vip_customers if c.get('phone') == customer_phone), None)
        
        return {
            "phone": customer_phone,
            "customer": {"phone": customer_phone},
            "metrics": {},
            "lifetime_value": {"historical": 0, "projected_12_month": 0},
            "calls": [
                {
                    "id": c.id,
                    "started_at": c.started_at.isoformat() if c.started_at else None,
                    "duration_seconds": c.duration_seconds,
                    "ai_confidence": float(c.ai_confidence) if c.ai_confidence else None,
                    "sentiment": c.sentiment,
                    "summary": c.summary,
                    "status": c.status
                }
                for c in calls
            ],
            "appointments": [
                {
                    "id": a.id,
                    "customer_name": a.customer_name,
                    "appointment_time": a.appointment_time.isoformat() if a.appointment_time else None,
                    "service_type": a.service_type,
                    "status": a.status
                }
                for a in appointments
            ],
            "churn_risk": churn_risk,
            "vip_status": vip_status,
            "insights": [],
            "recommendations": [],
            "stats": {
                "total_calls": len(calls),
                "total_appointments": len(appointments)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_customer_insights(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Get overall customer intelligence insights for a business.
    
    Returns:
    - Total unique customers
    - VIP customer count
    - High risk churn count
    - Customer segments (from Customer 360)
    - Recent complaint trends
    """
    try:
        # Get Customer 360 segments
        segments = await customer_360_service.get_customer_segments(db, business_id)
        
        # Get top customers
        top_customers = await customer_360_service.get_top_customers(db, business_id, limit=5, sort_by="lifetime_value")
        
        # Get unique customer count from Customer model
        total_customers = db.query(func.count(Customer.id)).filter(
            Customer.business_id == business_id
        ).scalar() or 0
        
        # If no Customer records, fall back to call sessions
        if total_customers == 0:
            total_customers = db.query(
                func.count(func.distinct(CallSession.customer_phone))
            ).filter(
                CallSession.business_id == business_id,
                CallSession.customer_phone.isnot(None)
            ).scalar() or 0
        
        # Get complaint patterns
        complaint_patterns = await customer_intelligence_service.detect_complaint_patterns(
            business_id=business_id,
            db=db,
            days=30
        )
        
        return {
            "total_customers": total_customers,
            "vip_count": segments.get("segments", {}).get("vip", {}).get("count", 0),
            "high_risk_count": segments.get("segments", {}).get("at_risk", {}).get("count", 0),
            "segments": segments,
            "top_customers": top_customers,
            "complaint_trends": complaint_patterns.get("trends", []),
            "top_issues": complaint_patterns.get("common_issues", [])[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segments")
async def get_customer_segments(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Get customer segments for targeted marketing.
    
    Returns segments from Customer 360:
    - VIP customers
    - At-risk customers
    - Loyal customers
    - New customers
    - Inactive customers
    """
    try:
        result = await customer_360_service.get_customer_segments(db, business_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top")
async def get_top_customers(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("lifetime_value", regex="^(lifetime_value|total_spent|total_orders)$")
):
    """
    Get top customers by various metrics using Customer 360 data.
    """
    try:
        result = await customer_360_service.get_top_customers(db, business_id, limit, sort_by)
        return {"customers": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/churn-risk/{customer_phone}")
async def get_churn_risk(
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Calculate churn risk for a specific customer
    
    Returns churn risk score (0-1), risk level, contributing factors,
    and actionable recommendations
    """
    try:
        # Try Customer 360 first
        profile = await customer_360_service.get_customer_profile(db, business_id, customer_phone)
        if "error" not in profile:
            metrics = profile.get("metrics", {})
            churn_risk = metrics.get("churn_risk", 0)
            insights = profile.get("insights", [])
            risk_insights = [i for i in insights if i.get("category") == "retention"]
            
            return {
                "churn_risk_score": churn_risk,
                "risk_level": "high" if churn_risk > 0.6 else "medium" if churn_risk > 0.3 else "low",
                "factors": {},
                "recommendations": [i.get("action", "") for i in risk_insights] if risk_insights else [],
                "insights": risk_insights
            }
        
        # Fallback to customer intelligence service
        result = await customer_intelligence_service.calculate_churn_risk(
            customer_phone=customer_phone,
            business_id=business_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vip-customers")
async def get_vip_customers(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    min_satisfaction: Optional[float] = 4.5,
    min_appointments: Optional[int] = 5
):
    """
    Identify VIP customers based on multiple criteria
    
    Returns list of VIP customers with their metrics and VIP tier
    """
    try:
        # Get from Customer 360 segments
        segments = await customer_360_service.get_customer_segments(db, business_id)
        vip_customers = segments.get("segments", {}).get("vip", {}).get("customers", [])
        
        if vip_customers:
            return {
                "total_vip_customers": len(vip_customers),
                "customers": vip_customers
            }
        
        # Fallback to customer intelligence service
        result = await customer_intelligence_service.identify_vip_customers(
            business_id=business_id,
            db=db,
            min_satisfaction=min_satisfaction,
            min_appointments=min_appointments
        )
        return {
            "total_vip_customers": len(result),
            "customers": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic-search")
async def semantic_search_history(
    query: str,
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    top_k: Optional[int] = 5
):
    """
    Semantic search across customer interaction history
    
    Search for similar interactions using natural language queries
    """
    try:
        results = await customer_intelligence_service.semantic_search_customer_history(
            query=query,
            customer_phone=customer_phone,
            business_id=business_id,
            db=db,
            top_k=top_k
        )
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complaint-patterns")
async def get_complaint_patterns(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db),
    days: Optional[int] = 90
):
    """
    Detect patterns in customer complaints
    
    Analyzes common complaint topics, trending issues, and provides recommendations
    """
    try:
        result = await customer_intelligence_service.detect_complaint_patterns(
            business_id=business_id,
            db=db,
            days=days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index-customer/{customer_phone}")
async def index_customer_history(
    customer_phone: str,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    """
    Index customer interaction history for semantic search
    
    Generates embeddings for all customer interactions
    """
    try:
        result = await customer_intelligence_service.index_customer_history(
            customer_phone=customer_phone,
            business_id=business_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))