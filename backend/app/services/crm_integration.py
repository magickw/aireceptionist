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
    
    # ==================== BI-DIRECTIONAL SYNC ====================
    
    async def fetch_salesforce_contact(self, contact_id: str) -> Dict[str, Any]:
        """Fetch a contact from Salesforce by ID"""
        if not all([self.sf_username, self.sf_password, self.sf_security_token]):
            return {"success": False, "error": "Salesforce not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Ensure we have an access token
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
                
                async with session.get(
                    f"{self.sf_instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "contact": data,
                            "first_name": data.get("FirstName"),
                            "last_name": data.get("LastName"),
                            "email": data.get("Email"),
                            "phone": data.get("Phone"),
                            "company": data.get("Company"),
                            "last_modified": data.get("LastModifiedDate")
                        }
                    else:
                        return {"success": False, "error": "Contact not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_salesforce_contact(
        self,
        contact_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing contact in Salesforce"""
        if not all([self.sf_username, self.sf_password, self.sf_security_token]):
            return {"success": False, "error": "Salesforce not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Ensure we have an access token
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
                
                payload = {}
                if first_name:
                    payload["FirstName"] = first_name
                if last_name:
                    payload["LastName"] = last_name
                if email:
                    payload["Email"] = email
                if phone:
                    payload["Phone"] = phone
                if company:
                    payload["Company"] = company
                
                if not payload:
                    return {"success": False, "error": "No fields to update"}
                
                async with session.patch(
                    f"{self.sf_instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status in [200, 204]:
                        return {
                            "success": True,
                            "contact_id": contact_id,
                            "updated": True
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to update contact: {error_data}"
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_hubspot_contact(self, contact_id: str) -> Dict[str, Any]:
        """Fetch a contact from HubSpot by ID"""
        if not self.hs_api_key:
            return {"success": False, "error": "HubSpot not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.hs_api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
                    headers=headers,
                    params={"properties": "email,firstname,lastname,phone,company,hs_lead_status"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        props = data.get("properties", {})
                        return {
                            "success": True,
                            "contact": data,
                            "first_name": props.get("firstname"),
                            "last_name": props.get("lastname"),
                            "email": props.get("email"),
                            "phone": props.get("phone"),
                            "company": props.get("company"),
                            "lead_status": props.get("hs_lead_status"),
                            "last_modified": data.get("updatedAt")
                        }
                    else:
                        return {"success": False, "error": "Contact not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_hubspot_contact(
        self,
        contact_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        lead_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing contact in HubSpot"""
        if not self.hs_api_key:
            return {"success": False, "error": "HubSpot not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.hs_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {"properties": {}}
                if first_name:
                    payload["properties"]["firstname"] = first_name
                if last_name:
                    payload["properties"]["lastname"] = last_name
                if phone:
                    payload["properties"]["phone"] = phone
                if company:
                    payload["properties"]["company"] = company
                if lead_status:
                    payload["properties"]["hs_lead_status"] = lead_status
                
                if not payload["properties"]:
                    return {"success": False, "error": "No fields to update"}
                
                async with session.patch(
                    f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "contact_id": contact_id,
                            "updated": True
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to update contact: {error_data}"
                        }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_salesforce_opportunities(self, contact_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Fetch opportunities from Salesforce, optionally filtered by contact"""
        if not all([self.sf_username, self.sf_password, self.sf_security_token]):
            return {"success": False, "error": "Salesforce not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Ensure we have an access token
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
                
                # Build SOQL query
                query = "SELECT Id, Name, StageName, Amount, CloseDate, Probability, LastModifiedDate FROM Opportunity"
                if contact_id:
                    query += f" WHERE ContactId = '{contact_id}'"
                query += f" LIMIT {limit}"
                
                params = {"q": query}
                
                async with session.get(
                    f"{self.sf_instance_url}/services/data/v58.0/query",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "opportunities": data.get("records", []),
                            "total": len(data.get("records", []))
                        }
                    else:
                        return {"success": False, "error": "Failed to fetch opportunities"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_hubspot_deals(self, contact_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Fetch deals from HubSpot, optionally filtered by contact"""
        if not self.hs_api_key:
            return {"success": False, "error": "HubSpot not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.hs_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Build query
                payload = {
                    "filterGroups": [],
                    "properties": ["dealname", "amount", "dealstage", "closedate", "hs_lastmodifieddate"],
                    "limit": limit
                }
                
                if contact_id:
                    payload["filterGroups"] = [{
                        "filters": [{
                            "propertyName": "associations.contact",
                            "operator": "EQ",
                            "value": contact_id
                        }]
                    }]
                
                async with session.post(
                    "https://api.hubapi.com/crm/v3/objects/deals/search",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "deals": data.get("results", []),
                            "total": len(data.get("results", []))
                        }
                    else:
                        return {"success": False, "error": "Failed to fetch deals"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sync_from_crm(
        self,
        crm_type: str,
        contact_id: str,
        local_customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync customer data FROM CRM to local database
        This is the bi-directional sync part - fetching updates made in CRM
        """
        if crm_type == "salesforce":
            result = await self.fetch_salesforce_contact(contact_id)
            if not result["success"]:
                return result
            
            contact = result["contact"]
            return {
                "success": True,
                "contact_id": contact_id,
                "first_name": contact.get("FirstName"),
                "last_name": contact.get("LastName"),
                "email": contact.get("Email"),
                "phone": contact.get("Phone"),
                "company": contact.get("Company"),
                "last_synced": datetime.utcnow(),
                "sync_direction": "crm_to_local"
            }
        
        elif crm_type == "hubspot":
            result = await self.fetch_hubspot_contact(contact_id)
            if not result["success"]:
                return result
            
            props = result["contact"].get("properties", {})
            return {
                "success": True,
                "contact_id": contact_id,
                "first_name": props.get("firstname"),
                "last_name": props.get("lastname"),
                "email": props.get("email"),
                "phone": props.get("phone"),
                "company": props.get("company"),
                "lead_status": props.get("hs_lead_status"),
                "last_synced": datetime.utcnow(),
                "sync_direction": "crm_to_local"
            }
        
        else:
            return {"success": False, "error": f"Unsupported CRM type: {crm_type}"}
    
    async def sync_to_crm(
        self,
        crm_type: str,
        contact_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync customer data TO CRM from local database
        Updates existing contact in CRM
        """
        if crm_type == "salesforce":
            name_parts = customer_data.get("name", "").split(" ", 1)
            return await self.update_salesforce_contact(
                contact_id=contact_id,
                first_name=name_parts[0] if name_parts else None,
                last_name=name_parts[1] if len(name_parts) > 1 else None,
                email=customer_data.get("email"),
                phone=customer_data.get("phone"),
                company=customer_data.get("company")
            )
        
        elif crm_type == "hubspot":
            name_parts = customer_data.get("name", "").split(" ", 1)
            return await self.update_hubspot_contact(
                contact_id=contact_id,
                first_name=name_parts[0] if name_parts else None,
                last_name=name_parts[1] if len(name_parts) > 1 else None,
                phone=customer_data.get("phone"),
                company=customer_data.get("company"),
                lead_status=customer_data.get("lead_status")
            )
        
        else:
            return {"success": False, "error": f"Unsupported CRM type: {crm_type}"}
    
    async def get_customer_history_from_crm(
        self,
        crm_type: str,
        contact_id: str
    ) -> Dict[str, Any]:
        """
        Fetch customer history (opportunities/deals, activities) from CRM
        Useful for Customer 360 and providing AI with full context
        """
        if crm_type == "salesforce":
            opp_result = await self.fetch_salesforce_opportunities(contact_id=contact_id)
            return {
                "success": opp_result["success"],
                "crm_type": "salesforce",
                "opportunities": opp_result.get("opportunities", []),
                "total_opportunities": opp_result.get("total", 0),
                "total_value": sum(o.get("Amount", 0) for o in opp_result.get("opportunities", []))
            }
        
        elif crm_type == "hubspot":
            deal_result = await self.fetch_hubspot_deals(contact_id=contact_id)
            return {
                "success": deal_result["success"],
                "crm_type": "hubspot",
                "deals": deal_result.get("deals", []),
                "total_deals": deal_result.get("total", 0),
                "total_value": sum(
                    float(d.get("properties", {}).get("amount", 0))
                    for d in deal_result.get("deals", [])
                )
            }
        
        else:
            return {"success": False, "error": f"Unsupported CRM type: {crm_type}"}


# Singleton instance
crm_integration = CRMIntegrationService()