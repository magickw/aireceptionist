"""
Customer Intelligence API Endpoints

Provides endpoints for:
- Churn risk analysis
- VIP customer identification
- Semantic search across customer history
- Complaint pattern detection
- Customer list and details
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List

from app.api import deps
from app.services.customer_intelligence import customer_intelligence_service
from app.models.models import CallSession, Appointment


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
    """
    try:
        # Get unique customer phones from call sessions
        offset = (page - 1) * page_size
        
        # Query for customer summary
        from sqlalchemy import func, cast, Float
        
        # Get call counts and customer info
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
        )
        
        # Get appointment counts
        appointment_stats = db.query(
            Appointment.customer_phone,
            func.count(Appointment.id).label('appointment_count')
        ).filter(
            Appointment.business_id == business_id,
            Appointment.customer_phone.isnot(None)
        ).group_by(
            Appointment.customer_phone
        )
        
        # Execute queries
        call_results = call_stats.all()
        appointment_results = appointment_stats.all()
        
        # Build customer list
        customer_map = {}
        
        for r in call_results:
            phone = r.customer_phone
            customer_map[phone] = {
                'phone': phone,
                'call_count': r.call_count or 0,
                'last_contact': r.last_contact.isoformat() if r.last_contact else None,
                'avg_confidence': float(r.avg_confidence) if r.avg_confidence else 0,
                'appointment_count': 0,
                'churn_risk': None,
                'vip_status': None
            }
        
        for r in appointment_results:
            phone = r.customer_phone
            if phone in customer_map:
                customer_map[phone]['appointment_count'] = r.appointment_count or 0
            else:
                customer_map[phone] = {
                    'phone': phone,
                    'call_count': 0,
                    'last_contact': None,
                    'avg_confidence': 0,
                    'appointment_count': r.appointment_count or 0,
                    'churn_risk': None,
                    'vip_status': None
                }
        
        # Convert to list
        customers = list(customer_map.values())
        
        # Sort
        if sort_by == 'last_contact':
            customers.sort(key=lambda x: x['last_contact'] or '', reverse=(sort_order == 'desc'))
        elif sort_by == 'call_count':
            customers.sort(key=lambda x: x['call_count'], reverse=(sort_order == 'desc'))
        elif sort_by == 'appointments':
            customers.sort(key=lambda x: x['appointment_count'], reverse=(sort_order == 'desc'))
        
        # Paginate
        total = len(customers)
        paginated_customers = customers[offset:offset + page_size]
        
        return {
            "customers": paginated_customers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
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
    
    Includes:
    - Churn risk analysis
    - VIP status
    - Recent calls
    - Appointments
    - Interaction history
    """
    try:
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
        
        # Get churn risk
        try:
            churn_risk = await customer_intelligence_service.calculate_churn_risk(
                customer_phone=customer_phone,
                business_id=business_id,
                db=db
            )
        except:
            churn_risk = None
        
        # Get VIP status
        try:
            vip_customers = await customer_intelligence_service.identify_vip_customers(
                business_id=business_id,
                db=db
            )
            vip_status = next((c for c in vip_customers if c.get('phone') == customer_phone), None)
        except:
            vip_status = None
        
        return {
            "phone": customer_phone,
            "calls": [
                {
                    "id": c.id,
                    "started_at": c.started_at.isoformat() if c.started_at else None,
                    "duration_seconds": c.duration_seconds,
                    "ai_confidence": float(c.ai_confidence) if c.ai_confidence else None,
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
    - Recent complaint trends
    """
    try:
        # Get unique customer count
        unique_customers = db.query(
            func.count(func.distinct(CallSession.customer_phone))
        ).filter(
            CallSession.business_id == business_id,
            CallSession.customer_phone.isnot(None)
        ).scalar() or 0
        
        # Get VIP customers
        vip_customers = await customer_intelligence_service.identify_vip_customers(
            business_id=business_id,
            db=db
        )
        
        # Get complaint patterns
        complaint_patterns = await customer_intelligence_service.detect_complaint_patterns(
            business_id=business_id,
            db=db,
            days=30
        )
        
        # Calculate high-risk churn customers
        # For now, estimate based on recent calls with low confidence
        high_risk_count = db.query(CallSession).filter(
            CallSession.business_id == business_id,
            CallSession.ai_confidence < 0.7
        ).count()
        
        return {
            "total_customers": unique_customers,
            "vip_count": len(vip_customers),
            "high_risk_count": high_risk_count,
            "complaint_trends": complaint_patterns.get("trends", []),
            "top_issues": complaint_patterns.get("common_issues", [])[:5]
        }
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