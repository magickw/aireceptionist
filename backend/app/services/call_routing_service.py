"""
Call Routing Service
Manages intelligent call routing rules
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import json


class CallRoutingService:
    """Service for managing call routing rules"""
    
    def __init__(self):
        self.rule_conditions = [
            "time_of_day",
            "day_of_week",
            "caller_id",
            "voicemail_detected",
            "call_duration",
            "previous_call_count"
        ]
        
        self.rule_actions = [
            "transfer_to_extension",
            "transfer_to_mobile",
            "send_to_voicemail",
            "play_announcement",
            "queue_call",
            "route_to_oncall"
        ]
    
    def create_rule(
        self,
        db: Session,
        business_id: int,
        name: str,
        conditions: Dict,
        action: str,
        action_value: str,
        priority: int = 100
    ) -> Dict:
        """Create a new routing rule"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise ValueError("Business not found")
        
        rule = {
            "id": int(datetime.now(timezone.utc).timestamp()),
            "name": name,
            "conditions": conditions,
            "action": action,
            "action_value": action_value,
            "priority": priority,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in business settings
        if not business.settings:
            business.settings = {}
        
        rules = business.settings.get("call_routing_rules", [])
        rules.append(rule)
        business.settings["call_routing_rules"] = rules
        db.commit()
        
        return rule
    
    def update_rule(
        self,
        db: Session,
        business_id: int,
        rule_id: int,
        is_active: bool = None,
        priority: int = None
    ) -> Dict:
        """Update a routing rule"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise ValueError("Business not found")
        
        rules = business.settings.get("call_routing_rules", [])
        
        for rule in rules:
            if rule.get("id") == rule_id:
                if is_active is not None:
                    rule["is_active"] = is_active
                if priority is not None:
                    rule["priority"] = priority
                rule["updated_at"] = datetime.now(timezone.utc).isoformat()
                break
        
        business.settings["call_routing_rules"] = rules
        db.commit()
        
        return rule
    
    def delete_rule(
        self,
        db: Session,
        business_id: int,
        rule_id: int
    ) -> bool:
        """Delete a routing rule"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return False
        
        rules = business.settings.get("call_routing_rules", [])
        original_length = len(rules)
        
        rules = [r for r in rules if r.get("id") != rule_id]
        
        if len(rules) < original_length:
            business.settings["call_routing_rules"] = rules
            db.commit()
            return True
        
        return False
    
    def get_rules(
        self,
        db: Session,
        business_id: int
    ) -> List[Dict]:
        """Get all routing rules for a business"""
        from app.models.models import Business
        
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return []
        
        rules = business.settings.get("call_routing_rules", [])
        return sorted(rules, key=lambda x: x.get("priority", 100))
    
    def evaluate_rules(
        self,
        db: Session,
        business_id: int,
        call_context: Dict
    ) -> Optional[Dict]:
        """Evaluate routing rules and return matched action"""
        rules = self.get_rules(db, business_id)
        
        for rule in rules:
            if not rule.get("is_active", True):
                continue
            
            if self._evaluate_conditions(rule.get("conditions", {}), call_context):
                return {
                    "action": rule.get("action"),
                    "action_value": rule.get("action_value"),
                    "rule_name": rule.get("name")
                }
        
        return None
    
    def _evaluate_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Evaluate if conditions match the call context"""
        if not conditions:
            return True
        
        # Time of day condition
        if "time_of_day" in conditions:
            current_hour = datetime.now(timezone.utc).hour
            time_range = conditions["time_of_day"]
            if isinstance(time_range, dict):
                start = time_range.get("start", 0)
                end = time_range.get("end", 23)
                if not (start <= current_hour <= end):
                    return False
        
        # Day of week condition
        if "day_of_week" in conditions:
            current_dow = datetime.now(timezone.utc).weekday()
            allowed_days = conditions["day_of_week"]
            if isinstance(allowed_days, list):
                if current_dow not in allowed_days:
                    return False
        
        # Caller ID condition
        if "caller_id" in conditions:
            caller = context.get("caller_id", "")
            pattern = conditions["caller_id"]
            if pattern.startswith("*"):
                # Ends with
                if not caller.endswith(pattern[1:]):
                    return False
            elif pattern.endswith("*"):
                # Starts with
                if not caller.startswith(pattern[:-1]):
                    return False
            elif caller != pattern:
                return False
        
        # Voicemail detected condition
        if "voicemail_detected" in conditions:
            is_voicemail = context.get("voicemail_detected", False)
            expected = conditions["voicemail_detected"]
            if is_voicemail != expected:
                return False
        
        return True
    
    def get_conditions_options(self) -> Dict:
        """Get available conditions and their options"""
        return {
            "conditions": self.rule_conditions,
            "actions": self.rule_actions,
            "examples": {
                "time_of_day": {"start": 9, "end": 17},
                "day_of_week": [0, 1, 2, 3, 4],  # Monday-Friday
                "caller_id": "+1234567890",
                "voicemail_detected": True,
                "call_duration": {"min": 0, "max": 30},
                "previous_call_count": {"min": 5}
            }
        }


call_routing_service = CallRoutingService()
