"""
Real Browser Automation Service using Playwright
Actual browser control for Nova Act automation workflows
"""

import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Browser, Page
import json

class BrowserAutomationService:
    """Real browser automation service using Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.screenshots: List[str] = []
    
    async def start_browser(self, headless: bool = True) -> bool:
        """Start a browser instance"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.page = await self.browser.new_page()
            return True
        except Exception as e:
            print(f"[Browser Automation] Failed to start browser: {e}")
            return False
    
    async def stop_browser(self) -> None:
        """Stop the browser and clean up"""
        if self.page:
            await self.page.close()
            self.page = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    async def navigate_to(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            screenshot = await self.page.screenshot()
            self.screenshots.append(f"navigate_{len(self.screenshots)}.png")
            
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "screenshot": f"navigate_{len(self.screenshots)-1}.png"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            for selector, value in form_data.items():
                await self.page.fill(selector, value)
            
            screenshot = await self.page.screenshot()
            self.screenshots.append(f"fill_{len(self.screenshots)}.png")
            
            return {
                "success": True,
                "fields_filled": len(form_data),
                "screenshot": f"fill_{len(self.screenshots)-1}.png"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click_element(self, selector: str) -> Dict[str, Any]:
        """Click an element"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            await self.page.click(selector)
            await self.page.wait_for_load_state("networkidle")
            
            screenshot = await self.page.screenshot()
            self.screenshots.append(f"click_{len(self.screenshots)}.png")
            
            return {
                "success": True,
                "element": selector,
                "screenshot": f"click_{len(self.screenshots)-1}.png"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {
                "success": True,
                "element": selector,
                "found": True
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_text(self, selector: str) -> Dict[str, Any]:
        """Extract text from an element"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            element = await self.page.query_selector(selector)
            if not element:
                return {"success": False, "error": "Element not found"}
            
            text = await element.inner_text()
            return {
                "success": True,
                "text": text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(self, name: Optional[str] = None) -> str:
        """Take a screenshot"""
        if not self.page:
            return ""
        
        try:
            filename = name or f"screenshot_{len(self.screenshots)}.png"
            await self.page.screenshot(path=filename)
            self.screenshots.append(filename)
            return filename
        except Exception as e:
            print(f"[Browser Automation] Failed to take screenshot: {e}")
            return ""
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            title = await self.page.title()
            url = self.page.url
            
            return {
                "success": True,
                "title": title,
                "url": url,
                "screenshot_count": len(self.screenshots)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_script(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript on the page"""
        if not self.page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            result = await self.page.evaluate(script)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
browser_automation = BrowserAutomationService()
