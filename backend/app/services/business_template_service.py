"""Database-driven business template service with caching and versioning"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.models import BusinessTemplate, TemplateVersion, User
from app.db.session import SessionLocal
from datetime import datetime
import json


class BusinessTemplateService:
    """Service for managing business templates from database"""
    
    def __init__(self):
        self._template_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps = {}
    
    def get_template(
        self,
        business_type: str,
        db: Session,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get business template by type.
        
        Args:
            business_type: Template key (e.g., 'restaurant', 'medical')
            db: Database session
            use_cache: Whether to use cached templates
        
        Returns:
            Template configuration dictionary
        """
        # Check cache
        if use_cache and business_type in self._template_cache:
            timestamp = self._cache_timestamps.get(business_type, 0)
            if (datetime.now().timestamp() - timestamp) < self._cache_ttl:
                return self._template_cache[business_type]
        
        # Load from database
        template = db.query(BusinessTemplate).filter(
            BusinessTemplate.template_key == business_type,
            BusinessTemplate.is_active == True
        ).first()
        
        if not template:
            # Fall back to general template
            template = db.query(BusinessTemplate).filter(
                BusinessTemplate.template_key == "general",
                BusinessTemplate.is_active == True
            ).first()
        
        if not template:
            raise ValueError(f"Template '{business_type}' not found and no default template available")
        
        # Convert to dictionary format matching original BusinessTypeTemplate
        template_dict = self._template_to_dict(template)
        
        # Cache it
        if use_cache:
            self._template_cache[business_type] = template_dict
            self._cache_timestamps[business_type] = datetime.now().timestamp()
        
        return template_dict
    
    def get_all_templates(
        self,
        db: Session,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all business templates"""
        query = db.query(BusinessTemplate)
        
        if active_only:
            query = query.filter(BusinessTemplate.is_active == True)
        
        templates = query.order_by(BusinessTemplate.name).all()
        
        return [self._template_to_dict(t) for t in templates]
    
    def get_template_by_id(
        self,
        template_id: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        template = db.query(BusinessTemplate).filter(
            BusinessTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        return self._template_to_dict(template)
    
    def create_template(
        self,
        template_data: Dict[str, Any],
        created_by: int,
        db: Session
    ) -> BusinessTemplate:
        """
        Create a new business template.
        
        Args:
            template_data: Template configuration
            created_by: User ID of creator
            db: Database session
        
        Returns:
            Created BusinessTemplate
        """
        template = BusinessTemplate(
            template_key=template_data["template_key"],
            name=template_data["name"],
            icon=template_data.get("icon"),
            description=template_data.get("description"),
            autonomy_level=template_data.get("autonomy_level", "MEDIUM"),
            high_risk_intents=template_data.get("risk_profile", {}).get("high_risk_intents"),
            auto_escalate_threshold=template_data.get("risk_profile", {}).get("auto_escalate_threshold"),
            confidence_threshold=template_data.get("risk_profile", {}).get("confidence_threshold"),
            common_intents=template_data.get("common_intents"),
            fields=template_data.get("fields"),
            booking_flow=template_data.get("booking_flow"),
            system_prompt_addition=template_data.get("system_prompt_addition"),
            example_responses=template_data.get("example_responses"),
            is_active=template_data.get("is_active", True),
            is_default=template_data.get("is_default", False),
            version=1,
            created_by=created_by,
        )
        
        db.add(template)
        db.flush()  # Get the ID
        
        # Create initial version
        self._create_version(template, template_data, "Initial version", created_by, db)
        
        db.commit()
        
        # Clear cache
        self._clear_cache(template.template_key)
        
        return template
    
    def update_template(
        self,
        template_id: int,
        template_data: Dict[str, Any],
        updated_by: int,
        db: Session
    ) -> Optional[BusinessTemplate]:
        """
        Update an existing business template.
        
        Args:
            template_id: Template ID
            template_data: Updated template configuration
            updated_by: User ID of updater
            db: Database session
        
        Returns:
            Updated BusinessTemplate or None if not found
        """
        template = db.query(BusinessTemplate).filter(
            BusinessTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        # Store old data for versioning
        old_data = self._template_to_dict(template)
        
        # Update fields
        if "name" in template_data:
            template.name = template_data["name"]
        if "icon" in template_data:
            template.icon = template_data["icon"]
        if "description" in template_data:
            template.description = template_data["description"]
        if "autonomy_level" in template_data:
            template.autonomy_level = template_data["autonomy_level"]
        if "risk_profile" in template_data:
            template.high_risk_intents = template_data["risk_profile"].get("high_risk_intents")
            template.auto_escalate_threshold = template_data["risk_profile"].get("auto_escalate_threshold")
            template.confidence_threshold = template_data["risk_profile"].get("confidence_threshold")
        if "common_intents" in template_data:
            template.common_intents = template_data["common_intents"]
        if "fields" in template_data:
            template.fields = template_data["fields"]
        if "booking_flow" in template_data:
            template.booking_flow = template_data["booking_flow"]
        if "system_prompt_addition" in template_data:
            template.system_prompt_addition = template_data["system_prompt_addition"]
        if "example_responses" in template_data:
            template.example_responses = template_data["example_responses"]
        if "is_active" in template_data:
            template.is_active = template_data["is_active"]
        if "is_default" in template_data:
            template.is_default = template_data["is_default"]
        
        # Increment version
        template.version += 1
        template.updated_at = datetime.now()
        
        # Create new version
        new_data = self._template_to_dict(template)
        self._create_version(
            template,
            new_data,
            template_data.get("change_description", "Template updated"),
            updated_by,
            db
        )
        
        db.commit()
        
        # Clear cache
        self._clear_cache(template.template_key)
        
        return template
    
    def delete_template(
        self,
        template_id: int,
        db: Session
    ) -> bool:
        """Delete a template (soft delete by setting is_active=False)"""
        template = db.query(BusinessTemplate).filter(
            BusinessTemplate.id == template_id
        ).first()
        
        if not template:
            return False
        
        # Prevent deleting default template
        if template.is_default:
            raise ValueError("Cannot delete default template")
        
        template.is_active = False
        template.updated_at = datetime.now()
        
        db.commit()
        
        # Clear cache
        self._clear_cache(template.template_key)
        
        return True
    
    def get_template_versions(
        self,
        template_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get all versions of a template"""
        versions = db.query(TemplateVersion).filter(
            TemplateVersion.template_id == template_id
        ).order_by(TemplateVersion.version_number.desc()).all()
        
        return [self._version_to_dict(v) for v in versions]
    
    def restore_version(
        self,
        version_id: int,
        restored_by: int,
        db: Session
    ) -> Optional[BusinessTemplate]:
        """
        Restore a template to a previous version.
        
        Args:
            version_id: Version ID to restore
            restored_by: User ID of restorer
            db: Database session
        
        Returns:
            Restored BusinessTemplate or None if not found
        """
        version = db.query(TemplateVersion).filter(
            TemplateVersion.id == version_id
        ).first()
        
        if not version:
            return None
        
        template = db.query(BusinessTemplate).filter(
            BusinessTemplate.id == version.template_id
        ).first()
        
        if not template:
            return None
        
        # Restore from version data
        template.name = version.name
        template.icon = version.icon
        template.description = version.description
        template.autonomy_level = version.autonomy_level
        template.high_risk_intents = version.high_risk_intents
        template.auto_escalate_threshold = version.auto_escalate_threshold
        template.confidence_threshold = version.confidence_threshold
        template.common_intents = version.common_intents
        template.fields = version.fields
        template.booking_flow = version.booking_flow
        template.system_prompt_addition = version.system_prompt_addition
        template.example_responses = version.example_responses
        
        # Increment version
        template.version += 1
        template.updated_at = datetime.now()
        
        # Create new version documenting the restore
        new_data = self._template_to_dict(template)
        self._create_version(
            template,
            new_data,
            f"Restored from version {version.version_number}",
            restored_by,
            db
        )
        
        db.commit()
        
        # Clear cache
        self._clear_cache(template.template_key)
        
        return template
    
    def _template_to_dict(self, template: BusinessTemplate) -> Dict[str, Any]:
        """Convert BusinessTemplate model to dictionary"""
        return {
            "id": template.id,
            "template_key": template.template_key,
            "name": template.name,
            "icon": template.icon,
            "description": template.description,
            "autonomy_level": template.autonomy_level,
            "risk_profile": {
                "high_risk_intents": template.high_risk_intents or [],
                "auto_escalate_threshold": float(template.auto_escalate_threshold) if template.auto_escalate_threshold else 0.5,
                "confidence_threshold": float(template.confidence_threshold) if template.confidence_threshold else 0.6,
            },
            "common_intents": template.common_intents or [],
            "fields": template.fields or {},
            "booking_flow": template.booking_flow or {},
            "system_prompt_addition": template.system_prompt_addition,
            "example_responses": template.example_responses or {},
            "is_active": template.is_active,
            "is_default": template.is_default,
            "version": template.version,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }
    
    def _version_to_dict(self, version: TemplateVersion) -> Dict[str, Any]:
        """Convert TemplateVersion model to dictionary"""
        return {
            "id": version.id,
            "template_id": version.template_id,
            "version_number": version.version_number,
            "name": version.name,
            "icon": version.icon,
            "description": version.description,
            "autonomy_level": version.autonomy_level,
            "high_risk_intents": version.high_risk_intents,
            "auto_escalate_threshold": float(version.auto_escalate_threshold) if version.auto_escalate_threshold else None,
            "confidence_threshold": float(version.confidence_threshold) if version.confidence_threshold else None,
            "common_intents": version.common_intents,
            "fields": version.fields,
            "booking_flow": version.booking_flow,
            "system_prompt_addition": version.system_prompt_addition,
            "example_responses": version.example_responses,
            "change_description": version.change_description,
            "is_active": version.is_active,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }
    
    def _create_version(
        self,
        template: BusinessTemplate,
        template_data: Dict[str, Any],
        description: str,
        created_by: int,
        db: Session
    ):
        """Create a template version"""
        version = TemplateVersion(
            template_id=template.id,
            version_number=template.version,
            name=template_data.get("name"),
            icon=template_data.get("icon"),
            description=template_data.get("description"),
            autonomy_level=template_data.get("autonomy_level"),
            high_risk_intents=template_data.get("risk_profile", {}).get("high_risk_intents"),
            auto_escalate_threshold=template_data.get("risk_profile", {}).get("auto_escalate_threshold"),
            confidence_threshold=template_data.get("risk_profile", {}).get("confidence_threshold"),
            common_intents=template_data.get("common_intents"),
            fields=template_data.get("fields"),
            booking_flow=template_data.get("booking_flow"),
            system_prompt_addition=template_data.get("system_prompt_addition"),
            example_responses=template_data.get("example_responses"),
            change_description=description,
            is_active=True,
            created_by=created_by,
        )
        
        db.add(version)
    
    def _clear_cache(self, business_type: str):
        """Clear cached template"""
        if business_type in self._template_cache:
            del self._template_cache[business_type]
        if business_type in self._cache_timestamps:
            del self._cache_timestamps[business_type]
    
    def clear_all_cache(self):
        """Clear all cached templates"""
        self._template_cache.clear()
        self._cache_timestamps.clear()


# Singleton instance
template_service = BusinessTemplateService()


def get_template(business_type: str, db: Session, use_cache: bool = True) -> Dict[str, Any]:
    """Convenience function for getting templates"""
    return template_service.get_template(business_type, db, use_cache)


def get_all_templates(db: Session, active_only: bool = True) -> List[Dict[str, Any]]:
    """Convenience function for getting all templates"""
    return template_service.get_all_templates(db, active_only)