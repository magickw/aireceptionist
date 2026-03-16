"""
Business Types API - Get available business type templates
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api import deps
from app.models.models import User
from app.services.business_templates import BusinessTypeTemplate

router = APIRouter()


class BusinessTypeInfo(BaseModel):
    type: str
    name: str
    icon: str
    common_intents: List[str]
    required_info: List[str]


@router.get("/types", response_model=List[BusinessTypeInfo])
def get_business_types() -> List[Dict[str, Any]]:
    """
    Get all available business type templates.
    """
    types = []
    for type_key in BusinessTypeTemplate.get_all_types():
        template = BusinessTypeTemplate.get_template(type_key)
        types.append({
            "type": type_key,
            "name": template.get("name", type_key.title()),
            "icon": template.get("icon", "business"),
            "common_intents": template.get("common_intents", []),
            "required_info": BusinessTypeTemplate.get_required_info(type_key),
        })
    return types


@router.get("/types/{business_type}")
def get_business_type_details(business_type: str) -> Dict[str, Any]:
    """
    Get detailed template for a specific business type.
    """
    template = BusinessTypeTemplate.get_template(business_type)
    return {
        "type": business_type,
        "name": template.get("name", business_type.title()),
        "icon": template.get("icon", "business"),
        "common_intents": template.get("common_intents", []),
        "required_info": BusinessTypeTemplate.get_required_info(business_type),
        "system_prompt_addition": template.get("system_prompt_addition", ""),
        "example_responses": template.get("example_responses", {})
    }
