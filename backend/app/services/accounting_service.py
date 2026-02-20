"""
Accounting Integration Service
QuickBooks and Xero integration for invoicing and financial sync
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import os
import requests
from urllib.parse import urlencode
from base64 import b64encode

from app.core.config import settings


class AccountingProvider:
    """Accounting provider types"""
    QUICKBOOKS = "quickbooks"
    XERO = "xero"


class QuickBooksService:
    """QuickBooks Online API integration"""
    
    BASE_URL = "https://quickbooks.api.intuit.com"
    SANDBOX_URL = "https://sandbox-quickbooks.api.intuit.com"
    
    def __init__(self, sandbox: bool = False):
        self.client_id = os.getenv('QUICKBOOKS_CLIENT_ID')
        self.client_secret = os.getenv('QUICKBOOKS_CLIENT_SECRET')
        self.realm_id = os.getenv('QUICKBOOKS_REALM_ID')
        self.refresh_token = os.getenv('QUICKBOOKS_REFRESH_TOKEN')
        self.sandbox = sandbox or os.getenv('QUICKBOOKS_SANDBOX', 'false').lower() == 'true'
        
        self.base_url = self.SANDBOX_URL if self.sandbox else self.BASE_URL
    
    def _get_auth_header(self, access_token: str) -> Dict:
        """Get authorization header"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def refresh_access_token(self, refresh_token: str = None) -> Dict:
        """Refresh QuickBooks access token"""
        
        refresh_token = refresh_token or self.refresh_token
        if not refresh_token:
            return {"error": "No refresh token available"}
        
        auth_string = b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        try:
            response = requests.post(
                "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in")
                }
            
            return {"error": response.json().get("error", "Token refresh failed")}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def create_invoice(
        self,
        access_token: str,
        customer_id: str,
        line_items: List[Dict],
        due_date: str = None,
        invoice_number: str = None
    ) -> Dict:
        """Create an invoice in QuickBooks"""
        
        invoice_data = {
            "Line": line_items,
            "CustomerRef": {
                "value": customer_id
            }
        }
        
        if due_date:
            invoice_data["DueDate"] = due_date
        
        if invoice_number:
            invoice_data["DocNumber"] = invoice_number
        
        try:
            response = requests.post(
                f"{self.base_url}/v3/company/{self.realm_id}/invoice",
                headers=self._get_auth_header(access_token),
                json=invoice_data
            )
            
            if response.status_code == 200:
                data = response.json()
                invoice = data.get("Invoice", {})
                return {
                    "success": True,
                    "invoice_id": invoice.get("Id"),
                    "invoice_number": invoice.get("DocNumber"),
                    "total": invoice.get("TotalAmt"),
                    "balance": invoice.get("Balance")
                }
            
            return {"error": response.json().get("Fault", {}).get("Error", [{}])[0].get("Message", "Invoice creation failed")}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_invoice(
        self,
        access_token: str,
        invoice_id: str
    ) -> Dict:
        """Get invoice details from QuickBooks"""
        
        try:
            response = requests.get(
                f"{self.base_url}/v3/company/{self.realm_id}/invoice/{invoice_id}",
                headers=self._get_auth_header(access_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                invoice = data.get("Invoice", {})
                return {
                    "success": True,
                    "invoice": {
                        "id": invoice.get("Id"),
                        "number": invoice.get("DocNumber"),
                        "total": invoice.get("TotalAmt"),
                        "balance": invoice.get("Balance"),
                        "status": "paid" if float(invoice.get("Balance", 0)) == 0 else "open",
                        "due_date": invoice.get("DueDate"),
                        "created_at": invoice.get("MetaData", {}).get("CreateTime")
                    }
                }
            
            return {"error": "Invoice not found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def create_customer(
        self,
        access_token: str,
        customer_data: Dict
    ) -> Dict:
        """Create a customer in QuickBooks"""
        
        try:
            response = requests.post(
                f"{self.base_url}/v3/company/{self.realm_id}/customer",
                headers=self._get_auth_header(access_token),
                json=customer_data
            )
            
            if response.status_code == 200:
                data = response.json()
                customer = data.get("Customer", {})
                return {
                    "success": True,
                    "customer_id": customer.get("Id"),
                    "display_name": customer.get("DisplayName")
                }
            
            return {"error": response.json().get("Fault", {}).get("Error", [{}])[0].get("Message", "Customer creation failed")}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def sync_orders_to_invoices(
        self,
        db: Session,
        business_id: int,
        access_token: str
    ) -> Dict:
        """Sync orders from database to QuickBooks invoices"""
        from app.models.models import Order
        
        orders = db.query(Order).filter(
            Order.business_id == business_id,
            Order.status == "completed",
            Order.quickbooks_invoice_id.is_(None)  # Not yet synced
        ).limit(50).all()
        
        synced = []
        failed = []
        
        for order in orders:
            line_items = []
            for item in order.items:
                line_items.append({
                    "Amount": float(item.unit_price * item.quantity),
                    "Description": item.item_name,
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "Qty": item.quantity,
                        "UnitPrice": float(item.unit_price)
                    }
                })
            
            result = await self.create_invoice(
                access_token=access_token,
                customer_id=order.customer_name,  # Should be QuickBooks customer ID
                line_items=line_items,
                invoice_number=f"ORD-{order.id}"
            )
            
            if result.get("success"):
                order.quickbooks_invoice_id = result["invoice_id"]
                synced.append(order.id)
            else:
                failed.append({"order_id": order.id, "error": result.get("error")})
        
        db.commit()
        
        return {
            "synced": len(synced),
            "failed": len(failed),
            "synced_orders": synced,
            "failed_orders": failed
        }


class XeroService:
    """Xero API integration"""
    
    BASE_URL = "https://api.xero.com/api.xro/2.0"
    AUTH_URL = "https://identity.xero.com/connect/token"
    
    def __init__(self):
        self.client_id = os.getenv('XERO_CLIENT_ID')
        self.client_secret = os.getenv('XERO_CLIENT_SECRET')
        self.tenant_id = os.getenv('XERO_TENANT_ID')
        self.refresh_token = os.getenv('XERO_REFRESH_TOKEN')
    
    def _get_auth_header(self, access_token: str) -> Dict:
        """Get authorization header"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Xero-tenant-id": self.tenant_id
        }
    
    async def refresh_access_token(self, refresh_token: str = None) -> Dict:
        """Refresh Xero access token"""
        
        refresh_token = refresh_token or self.refresh_token
        if not refresh_token:
            return {"error": "No refresh token available"}
        
        auth_string = b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        try:
            response = requests.post(
                self.AUTH_URL,
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in")
                }
            
            return {"error": response.json().get("error", "Token refresh failed")}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def create_invoice(
        self,
        access_token: str,
        contact_id: str,
        line_items: List[Dict],
        due_date: str = None,
        invoice_number: str = None,
        reference: str = None
    ) -> Dict:
        """Create an invoice in Xero"""
        
        invoice_data = {
            "Type": "ACCREC",  # Accounts Receivable
            "Contact": {
                "ContactID": contact_id
            },
            "LineItems": line_items,
            "Status": "AUTHORISED"  # Draft, Submitted, Authorised
        }
        
        if due_date:
            invoice_data["DueDate"] = due_date
        
        if invoice_number:
            invoice_data["InvoiceNumber"] = invoice_number
        
        if reference:
            invoice_data["Reference"] = reference
        
        try:
            response = requests.put(
                f"{self.BASE_URL}/Invoices",
                headers=self._get_auth_header(access_token),
                json={"Invoices": [invoice_data]}
            )
            
            if response.status_code == 200:
                data = response.json()
                invoice = data.get("Invoices", [{}])[0]
                return {
                    "success": True,
                    "invoice_id": invoice.get("InvoiceID"),
                    "invoice_number": invoice.get("InvoiceNumber"),
                    "total": invoice.get("Total"),
                    "amount_due": invoice.get("AmountDue")
                }
            
            return {"error": response.json().get("Elements", [{}])[0].get("ValidationErrors", [{}])[0].get("Message", "Invoice creation failed")}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_invoice(
        self,
        access_token: str,
        invoice_id: str
    ) -> Dict:
        """Get invoice details from Xero"""
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/Invoices/{invoice_id}",
                headers=self._get_auth_header(access_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                invoice = data.get("Invoices", [{}])[0]
                return {
                    "success": True,
                    "invoice": {
                        "id": invoice.get("InvoiceID"),
                        "number": invoice.get("InvoiceNumber"),
                        "total": invoice.get("Total"),
                        "amount_due": invoice.get("AmountDue"),
                        "status": invoice.get("Status"),
                        "due_date": invoice.get("DueDate"),
                        "date": invoice.get("Date")
                    }
                }
            
            return {"error": "Invoice not found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def create_contact(
        self,
        access_token: str,
        contact_data: Dict
    ) -> Dict:
        """Create a contact in Xero"""
        
        try:
            response = requests.put(
                f"{self.BASE_URL}/Contacts",
                headers=self._get_auth_header(access_token),
                json={"Contacts": [contact_data]}
            )
            
            if response.status_code == 200:
                data = response.json()
                contact = data.get("Contacts", [{}])[0]
                return {
                    "success": True,
                    "contact_id": contact.get("ContactID"),
                    "name": contact.get("Name")
                }
            
            return {"error": response.json().get("Elements", [{}])[0].get("ValidationErrors", [{}])[0].get("Message", "Contact creation failed")}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_contacts(
        self,
        access_token: str,
        page: int = 1
    ) -> Dict:
        """Get contacts from Xero"""
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/Contacts?page={page}",
                headers=self._get_auth_header(access_token)
            )
            
            if response.status_code == 200:
                data = response.json()
                contacts = data.get("Contacts", [])
                return {
                    "success": True,
                    "contacts": [
                        {
                            "id": c.get("ContactID"),
                            "name": c.get("Name"),
                            "email": c.get("EmailAddress"),
                            "phone": c.get("Phones", [{}])[0].get("PhoneNumber") if c.get("Phones") else None
                        }
                        for c in contacts
                    ]
                }
            
            return {"error": "Failed to get contacts"}
            
        except Exception as e:
            return {"error": str(e)}


class AccountingIntegrationService:
    """Main service for accounting integrations"""
    
    def __init__(self):
        self.quickbooks = QuickBooksService()
        self.xero = XeroService()
    
    async def get_service(self, provider: str):
        """Get the appropriate accounting service"""
        if provider == AccountingProvider.QUICKBOOKS:
            return self.quickbooks
        elif provider == AccountingProvider.XERO:
            return self.xero
        return None
    
    async def sync_data(
        self,
        db: Session,
        business_id: int,
        provider: str,
        access_token: str
    ) -> Dict:
        """Sync data between the app and accounting provider"""
        
        service = await self.get_service(provider)
        if not service:
            return {"error": "Invalid provider"}
        
        # Sync orders to invoices
        if provider == AccountingProvider.QUICKBOOKS:
            return await service.sync_orders_to_invoices(db, business_id, access_token)
        elif provider == AccountingProvider.XERO:
            # Similar implementation for Xero
            return {"synced": 0, "message": "Xero sync not yet implemented"}
    
    async def create_invoice_from_order(
        self,
        db: Session,
        order_id: int,
        provider: str,
        access_token: str
    ) -> Dict:
        """Create an invoice from an order"""
        from app.models.models import Order
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"error": "Order not found"}
        
        service = await self.get_service(provider)
        if not service:
            return {"error": "Invalid provider"}
        
        # Build line items
        line_items = []
        for item in order.items:
            line_items.append({
                "Description": item.item_name,
                "Quantity": item.quantity,
                "UnitAmount": float(item.unit_price)
            })
        
        # Create invoice
        result = await service.create_invoice(
            access_token=access_token,
            customer_id=order.customer_phone,  # Should map to contact
            line_items=line_items,
            invoice_number=f"ORD-{order.id}",
            reference=f"Order #{order.id}"
        )
        
        if result.get("success"):
            # Store invoice reference
            order.accounting_invoice_id = result.get("invoice_id")
            db.commit()
        
        return result
    
    def get_oauth_url(
        self,
        provider: str,
        redirect_uri: str,
        state: str = None
    ) -> str:
        """Get OAuth authorization URL for accounting provider"""
        
        if provider == AccountingProvider.QUICKBOOKS:
            params = {
                "client_id": os.getenv('QUICKBOOKS_CLIENT_ID'),
                "response_type": "code",
                "scope": "com.intuit.quickbooks.accounting",
                "redirect_uri": redirect_uri,
                "state": state or ""
            }
            return f"https://appcenter.intuit.com/connect/oauth2?{urlencode(params)}"
        
        elif provider == AccountingProvider.XERO:
            params = {
                "client_id": os.getenv('XERO_CLIENT_ID'),
                "response_type": "code",
                "scope": "openid profile email accounting.transactions accounting.contacts",
                "redirect_uri": redirect_uri,
                "state": state or ""
            }
            return f"https://login.xero.com/identity/connect/authorize?{urlencode(params)}"
        
        return ""


# Singleton instance
accounting_service = AccountingIntegrationService()
