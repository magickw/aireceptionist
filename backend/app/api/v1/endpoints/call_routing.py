"""
Call Routing API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.api import deps
from app.services.call_routing_service import call_routing_service


router = APIRouter()


class RoutingRuleCreate(BaseModel):
    name: str
    conditions: Dict[str, Any]
    action: str
    action_value: str
    priority: int = 100


class RoutingRuleUpdate(BaseModel):
    is_active: Optional[bool] = None
    priority: Optional[int] = None


@router.get("/options")
async def get_routing_options():
    options = call_routing_service.get_conditions_options()
    return options


@router.get("")
async def list_routing_rules(
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    rules = call_routing_service.get_rules(db, business_id)
    return {"rules": rules}


@router.post("")
async def create_routing_rule(
    rule_data: RoutingRuleCreate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    try:
        rule = call_routing_service.create_rule(
            db=db,
            business_id=business_id,
            name=rule_data.name,
            conditions=rule_data.conditions,
            action=rule_data.action,
            action_value=rule_data.action_value,
            priority=rule_data.priority
        )
        return {"success": True, "rule": rule}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@router.put("/{rule_id}")
async def update_routing_rule(
    rule_id: int,
    rule_data: RoutingRuleUpdate,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    try:
        rule = call_routing_service.update_rule(
            db=db,
            business_id=business_id,
            rule_id=rule_id,
            is_active=rule_data.is_active,
            priority=rule_data.priority
        )
        return {"success": True, "rule": rule}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@router.delete("/{rule_id}")
async def delete_routing_rule(
    rule_id: int,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    success = call_routing_service.delete_rule(db, business_id, rule_id)
    return {"success": success}


@router.post("/evaluate")
async def evaluate_routing(
    call_context: Dict[str, Any],
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    result = call_routing_service.evaluate_rules(db, business_id, call_context)
    return {"action": result}
