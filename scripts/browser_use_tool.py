from typing import Dict, List, Optional, Any, Union
import asyncio
import json

from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext
from browser_use.dom.service import DomService

from smolagents import Tool


class BrowserNavigationTool(Tool):
    """Tool to navigate to a URL in the browser."""
    name = "browser_navigate"
    description = "Navigate the browser to a specified URL and return the page content."
    inputs = {"url": {"type": "string", "description": "The URL to navigate to."}}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, url: str) -> str:
        result = await self.browser_manager.navigate(url)
        return f"Navigated to: {url}\n======================\n{result}"


class BrowserClickTool(Tool):
    """Tool to click on an element in the browser."""
    name = "browser_click"
    description = "Click on an element at a specified index in the browser page."
    inputs = {"index": {"type": "integer", "description": "The index of the element to click on."}}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, index: int) -> str:
        result = await self.browser_manager.click(index)
        return f"Clicked element at index {index}\n======================\n{result}"


class BrowserInputTextTool(Tool):
    """Tool to input text into an element in the browser."""
    name = "browser_input_text"
    description = "Input text into an element at a specified index in the browser page."
    inputs = {
        "index": {"type": "integer", "description": "The index of the element to input text into."},
        "text": {"type": "string", "description": "The text to input into the element."}
    }
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, index: int, text: str) -> str:
        result = await self.browser_manager.input_text(index, text)
        return f"Input text '{text}' into element at index {index}\n======================\n{result}"


class BrowserGetHtmlTool(Tool):
    """Tool to get the HTML content of the current page."""
    name = "browser_get_html"
    description = "Get the HTML content of the current page."
    inputs = {}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self) -> str:
        result = await self.browser_manager.get_html()
        return f"HTML content of the current page:\n======================\n{result}"


class BrowserGetTextTool(Tool):
    """Tool to get the text content of the current page."""
    name = "browser_get_text"
    description = "Get the text content of the current page."
    inputs = {}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self) -> str:
        result = await self.browser_manager.get_text()
        return f"Text content of the current page:\n======================\n{result}"


class BrowserScrollTool(Tool):
    """Tool to scroll the browser page."""
    name = "browser_scroll"
    description = "Scroll the browser page by a specified amount of pixels (positive for down, negative for up)."
    inputs = {"amount": {"type": "integer", "description": "The number of pixels to scroll (positive for down, negative for up)."}}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, amount: int) -> str:
        direction = "down" if amount > 0 else "up"
        result = await self.browser_manager.scroll(amount)
        return f"Scrolled {direction} by {abs(amount)} pixels\n======================\n{result}"


class BrowserSwitchTabTool(Tool):
    """Tool to switch between browser tabs."""
    name = "browser_switch_tab"
    description = "Switch to a different tab in the browser by specifying the tab ID."
    inputs = {"tab_id": {"type": "integer", "description": "The ID of the tab to switch to."}}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, tab_id: int) -> str:
        result = await self.browser_manager.switch_tab(tab_id)
        return f"Switched to tab {tab_id}\n======================\n{result}"


class BrowserNewTabTool(Tool):
    """Tool to open a new browser tab."""
    name = "browser_new_tab"
    description = "Open a new tab in the browser and navigate to the specified URL."
    inputs = {"url": {"type": "string", "description": "The URL to navigate to in the new tab."}}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, url: str) -> str:
        result = await self.browser_manager.new_tab(url)
        return f"Opened new tab with URL: {url}\n======================\n{result}"


class BrowserCloseTabTool(Tool):
    """Tool to close the current browser tab."""
    name = "browser_close_tab"
    description = "Close the current tab in the browser."
    inputs = {}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self) -> str:
        result = await self.browser_manager.close_tab()
        return f"Closed current tab\n======================\n{result}"


class BrowserRefreshTool(Tool):
    """Tool to refresh the current browser page."""
    name = "browser_refresh"
    description = "Refresh the current page in the browser."
    inputs = {}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self) -> str:
        result = await self.browser_manager.refresh()
        return f"Refreshed current page\n======================\n{result}"


class BrowserExecuteJsTool(Tool):
    """Tool to execute JavaScript in the browser."""
    name = "browser_execute_js"
    description = "Execute JavaScript code in the browser and return the result."
    inputs = {"script": {"type": "string", "description": "The JavaScript code to execute."}}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self, script: str) -> str:
        result = await self.browser_manager.execute_js(script)
        return f"Executed JavaScript:\n{script}\n======================\nResult: {result}"


class BrowserScreenshotTool(Tool):
    """Tool to take a screenshot of the current page."""
    name = "browser_screenshot"
    description = "Take a screenshot of the current page."
    inputs = {}
    output_type = "string"

    def __init__(self, browser_manager):
        super().__init__()
        self.browser_manager = browser_manager

    async def forward(self) -> str:
        result = await self.browser_manager.screenshot()
        return f"Screenshot taken. Base64 image data length: {len(result)}"


class BrowserManager:
    """Manager class for browser interactions using browser-use library."""
    
    def __init__(self, headless: bool = False):
        self.lock = asyncio.Lock()
        self.browser = None
        self.context = None
        self.dom_service = None
        self.headless = headless
        self.current_url = None
    
    async def _ensure_browser_initialized(self) -> BrowserContext:
        """Ensure browser and context are initialized."""
        if self.browser is None:
            self.browser = BrowserUseBrowser(BrowserConfig(headless=self.headless))
        if self.context is None:
            self.context = await self.browser.new_context()
            self.dom_service = DomService(await self.context.get_current_page())
        return self.context
    
    async def navigate(self, url: str) -> str:
        """Navigate to a URL and return the page content."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            await context.navigate_to(url)
            self.current_url = url
            return await self.get_text()
    
    async def click(self, index: int) -> str:
        """Click an element at the specified index and return the page state."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            element = await context.get_dom_element_by_index(index)
            if not element:
                return f"Error: Element with index {index} not found"
            download_path = await context._click_element_node(element)
            output = f"Clicked element at index {index}"
            if download_path:
                output += f" - Downloaded file to {download_path}"
            return output
    
    async def input_text(self, index: int, text: str) -> str:
        """Input text into an element at the specified index."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            element = await context.get_dom_element_by_index(index)
            if not element:
                return f"Error: Element with index {index} not found"
            await context._input_text_element_node(element, text)
            return f"Input '{text}' into element at index {index}"
    
    async def get_html(self) -> str:
        """Get the HTML content of the current page."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            html = await context.get_page_html()
            return html[:2000] + "..." if len(html) > 2000 else html
    
    async def get_text(self) -> str:
        """Get the text content of the current page."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            text = await context.execute_javascript("document.body.innerText")
            return text
    
    async def scroll(self, amount: int) -> str:
        """Scroll the page by the specified amount."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            await context.execute_javascript(f"window.scrollBy(0, {amount});")
            direction = "down" if amount > 0 else "up"
            return f"Scrolled {direction} by {abs(amount)} pixels"
    
    async def execute_js(self, script: str) -> str:
        """Execute JavaScript code and return the result."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            result = await context.execute_javascript(script)
            return str(result)
    
    async def screenshot(self) -> str:
        """Take a screenshot and return it as a base64 string."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            screenshot = await context.take_screenshot(full_page=True)
            return screenshot
            
    async def switch_tab(self, tab_id: int) -> str:
        """Switch to a specific tab by ID."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            await context.switch_to_tab(tab_id)
            return f"Switched to tab {tab_id}"
    
    async def new_tab(self, url: str) -> str:
        """Create a new tab and navigate to the specified URL."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            await context.create_new_tab(url)
            return f"Opened new tab with URL {url}"
    
    async def close_tab(self) -> str:
        """Close the current tab."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            await context.close_current_tab()
            return "Closed current tab"
    
    async def refresh(self) -> str:
        """Refresh the current page."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            await context.refresh_page()
            return "Refreshed current page"
    
    async def get_state(self) -> Dict[str, Any]:
        """Get the current browser state."""
        async with self.lock:
            context = await self._ensure_browser_initialized()
            state = await context.get_state()
            state_info = {
                "url": state.url,
                "title": state.title,
                "tabs": [tab.model_dump() for tab in state.tabs],
                "interactive_elements": state.element_tree.clickable_elements_to_string(),
            }
            return state_info
    
    async def cleanup(self):
        """Clean up browser resources."""
        async with self.lock:
            if self.context is not None:
                await self.context.close()
                self.context = None
                self.dom_service = None
            if self.browser is not None:
                await self.browser.close()
                self.browser = None


# Example usage
async def main():
    browser_manager = BrowserManager(headless=False)
    
    # Create tools
    navigate_tool = BrowserNavigationTool(browser_manager)
    click_tool = BrowserClickTool(browser_manager)
    input_tool = BrowserInputTextTool(browser_manager)
    get_text_tool = BrowserGetTextTool(browser_manager)
    switch_tab_tool = BrowserSwitchTabTool(browser_manager)
    new_tab_tool = BrowserNewTabTool(browser_manager)
    close_tab_tool = BrowserCloseTabTool(browser_manager)
    refresh_tool = BrowserRefreshTool(browser_manager)
    
    # Example: Navigate to a page
    result = await navigate_tool.forward("https://www.example.com")
    print(result)
    
    # Don't forget to clean up
    await browser_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())