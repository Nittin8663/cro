from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger("CromaStockAlert.checker")

def check_stock_with_selenium(url, product_name):
    """
    Check if a product is in stock on Croma by examining the Add to Cart button
    
    Args:
        url (str): URL of the product page on Croma
        product_name (str): Name of the product for logging
        
    Returns:
        bool: True if product is in stock, False otherwise
    """
    logger.info(f"Checking stock for {product_name}")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless to avoid browser UI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add realistic user agent to avoid detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # Initialize driver
    driver = None
    
    try:
        logger.debug("Initializing Chrome driver")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to the product page
        logger.debug(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load completely
        time.sleep(5)
        
        # Take screenshot for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/{product_name.replace(' ', '_')}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.debug(f"Saved screenshot to {screenshot_path}")
        
        # Check for Add to Cart button
        logger.debug("Looking for Add to Cart button")
        add_to_cart_selectors = [
            'button[data-testid="add-to-cart"]',
            'button.pdp-action',
            'button.add-to-cart',
            'button.buy-button',
            'button.addToCart',
            '[data-testid="addToCartButton"]'
        ]
        
        # Try different selector patterns for the Add to Cart button
        for selector in add_to_cart_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            if buttons:
                logger.debug(f"Found {len(buttons)} button(s) matching selector: {selector}")
                
                # Check if any button is not disabled
                for button in buttons:
                    is_disabled = button.get_attribute('disabled') == 'true' or 'disabled' in button.get_attribute('class')
                    button_text = button.text.strip()
                    
                    logger.debug(f"Button text: '{button_text}', Disabled: {is_disabled}")
                    
                    # If button is not disabled and contains relevant text, product is in stock
                    if not is_disabled and any(text in button_text.lower() for text in ['add to cart', 'buy now']):
                        logger.info(f"Product {product_name} is IN STOCK! (Add to Cart button is enabled)")
                        return True
        
        # If we couldn't find an enabled Add to Cart button, product is out of stock
        logger.info(f"Product {product_name} is OUT OF STOCK (Add to Cart button is disabled or not found)")
        return False
        
    except Exception as e:
        logger.error(f"Error checking stock for {product_name}: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()
            logger.debug("Chrome driver closed")