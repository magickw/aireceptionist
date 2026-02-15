"""
Real CRM Integration Service
Supports Salesforce and HubSpot integrations
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from app.core.config import settings

class CRMIntegrationService:
    """Service for real CRM integrations"""
    
    def __init__(self):
        # Salesforce config
        self.sf_username = settings.SALESFORCE_USERNAME if hasattr(settings, 'SALESFORCE_USERNAME') else os.environ.get('SALESFORCE_USERNAME')
        self.sf_password = settings.SALESFORCE_PASSWORD if hasattr(settings, 'SALESFORCE_PASSWORD') else os.environ.get('SALESFORCE_PASSWORD')
        self.sf_security_token = settings.SALESFORCE_SECURITY_TOKEN if hasattr(settings, 'SALESFORCE_SECURITY_TOKEN') else os.environ.get('SALESFORCE_SECURITY_TOKEN')
        self.sf_instance_url = None
        self.sf_access_token = None
        
        # HubSpot config
        self.hs_api_key = settings.HUBSPOT_API_KEY if hasattr(settings, 'HUBSPOT_API_KEY') else os.environ.get('HUBSPOT_API_KEY')
    
    async def create_salesforce_contact(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a contact in Salesforce using REST API"""
        if not all([self.sf_username, self.sf_password, self.sf_security_token]):
            return {"success": False, "error": "Salesforce not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # First, authenticate to get access token
                auth_url = "https://login.salesforce.com/services/oauth2/token"
                auth_data = {
                    "grant_type": "password",
                    "client_id": self.sf_username,
                    "client_secret": self.sf_password,
                    "username": self.sf_username,
                    "password": self.sf_password + self.sf_security_token
                }
                
                async with session.post(auth_url, data=auth_data) as auth_response:
                    if auth_response.status != 200:
                        return {"success": False, "error": "Salesforce authentication failed"}
                    
                    auth_result = await auth_response.json()
                    self.sf_access_token = auth_result["access_token"]
                    self.sf_instance_url = auth_result["instance_url"]
                
                # Create contact
                headers = {
                    "Authorization": f"Bearer {self.sf_access_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "FirstName": first_name,
                    "LastName": last_name,
                    "Email": email
                }
                
                if phone:
                    payload["Phone"] = phone
                if company:
                    payload["Company"] = company
                
                async with session.post(
                    f"{self.sf_instance_url}/services/data/v58.0/sobjects/Contact",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            "success": True,
                            "contact_id": data["id"],
                            "contact": data
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to create contact: {error_data}"
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_hubspot_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a contact in HubSpot"""
        if not self.hs_api_key:
            return {"success": False, "error": "HubSpot not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.hs_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Get or create contact by email
                async with session.post(
                    f"https://api.hubapi.com/crm/v3/objects/contacts/search",
                    headers=headers,
                    json={
                        "filterGroups": [{
                            "filters": [{
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email
                            }]
                        }]
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results") and len(data["results"]) > 0:
                            # Contact exists
                            return {
                                "success": True,
                                "contact_id": data["results"][0]["id"],
                                "created": False
                            }
                
                # Create new contact
                payload = {
                    "properties": {
                        "email": email
                    }
                }
                
                if first_name:
                    payload["properties"]["firstname"] = first_name
                if last_name:
                    payload["properties"]["lastname"] = last_name
                if phone:
                    payload["properties"]["phone"] = phone
                if company:
                    payload["properties"]["company"] = company
                
                async with session.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            "success": True,
                            "contact_id": data["id"],
                            "created": True,
                            "contact": data
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to create contact: {error_data}"
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_customer_to_crm(
        self,
        crm_type: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync customer data to CRM"""
        if crm_type == "salesforce":
            name_parts = customer_data.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            return await self.create_salesforce_contact(
                first_name=first_name,
                last_name=last_name,
                email=customer_data.get("email"),
                phone=customer_data.get("phone"),
                company=customer_data.get("company")
            )
        elif crm_type == "hubspot":
            name_parts = customer_data.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            return await self.create_hubspot_contact(
                email=customer_data.get("email"),
                first_name=first_name,
                last_name=last_name,
                phone=customer_data.get("phone"),
                company=customer_data.get("company")
            )
        else:
            return {
                "success": False,
                "error": f"Unsupported CRM type: {crm_type}"
            }
    
    async def create_hubspot_deal(
        self,
        deal_name: str,
        amount: float,
        stage: str = "appointmentscheduled",
        contact_id: Optional[str] = None,
        close_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a deal in HubSpot"""
        if not self.hs_api_key:
            return {"success": False, "error": "HubSpot not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.hs_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "properties": {
                        "dealname": deal_name,
                        "amount": amount,
                        "dealstage": stage
                    }
                }
                
                if contact_id:
                    payload["associations"] = [{
                        "to": {"id": contact_id},
                        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]
                    }]
                
                if close_date:
                    payload["properties"]["closedate"] = close_date
                
                async with session.post(
                    "https://api.hubapi.com/crm/v3/objects/deals",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            "success": True,
                            "deal_id": data["id"],
                            "deal": data
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to create deal: {error_data}"
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_salesforce_opportunity(
        self,
        opportunity_name: str,
        amount: float,
        stage: str = "Prospecting",
        contact_id: Optional[str] = None,
        close_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an opportunity in Salesforce"""
        if not all([self.sf_username, self.sf_password, self.sf_security_token]):
            return {"success": False, "error": "Salesforce not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Reuse or refresh access token
                if not self.sf_access_token:
                    auth_url = "https://login.salesforce.com/services/oauth2/token"
                    auth_data = {
                        "grant_type": "password",
                        "client_id": self.sf_username,
                        "client_secret": self.sf_password,
                        "username": self.sf_username,
                        "password": self.sf_password + self.sf_security_token
                    }
                    
                    async with session.post(auth_url, data=auth_data) as auth_response:
                        if auth_response.status != 200:
                            return {"success": False, "error": "Salesforce authentication failed"}
                        
                        auth_result = await auth_response.json()
                        self.sf_access_token = auth_result["access_token"]
                        self.sf_instance_url = auth_result["instance_url"]
                
                headers = {
                    "Authorization": f"Bearer {self.sf_access_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "Name": opportunity_name,
                    "StageName": stage,
                    "Amount": amount
                }
                
                if contact_id:
                    payload["ContactId"] = contact_id
                
                if close_date:
                    payload["CloseDate"] = close_date
                
                async with session.post(
                    f"{self.sf_instance_url}/services/data/v58.0/sobjects/Opportunity",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            "success": True,
                            "opportunity_id": data["id"],
                            "opportunity": data
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to create opportunity: {error_data}"
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
crm_integration = CRMIntegrationService()