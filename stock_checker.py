import requests
import json
import logging
import time
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("croma_stock_alert.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CromaStockAlert")

def check_stock_with_requests(url, product_name):
    """Improved stock checking function with better detection logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.croma.com/',
        'Connection': 'keep-alive',
        # Additional headers to appear more like a real browser
        'sec-ch-ua': '"Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    try:
        logger.info(f"Checking stock for {product_name} at {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            logger.info(f"Successfully loaded page for {product_name}")
            
            # Create directory for HTML responses if it doesn't exist
            os.makedirs("responses", exist_ok=True)
            
            # Save the response for debugging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"responses/{product_name.replace(' ', '_')}_{timestamp}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.info(f"Saved HTML response to {filename} for inspection")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = response.text.lower()
            
            # DETECTION METHOD 1: Check for explicit "In Stock" text
            stock_status_elements = soup.select('.stock-status, .pdp-stock, [data-testid="stock-status"]')
            for element in stock_status_elements:
                text = element.text.strip().lower()
                logger.info(f"Found stock status element with text: '{text}'")
                if "in stock" in text:
                    logger.info(f"✅ Product {product_name} is IN STOCK! (Found 'in stock' text)")
                    return True
                if any(x in text for x in ["out of stock", "sold out", "currently unavailable"]):
                    logger.info(f"❌ Product {product_name} is OUT OF STOCK (Found out of stock text)")
                    return False
            
            # DETECTION METHOD 2: Check for Add to Cart buttons
            add_to_cart_patterns = [
                'button[data-testid="add-to-cart"]',
                '.pdp-action', 
                '.add-to-cart',
                '.buy-button',
                '[data-testid="addToCartButton"]',
                'button:contains("Add to Cart")',
                'button:contains("Buy Now")'
            ]
            
            for pattern in add_to_cart_patterns:
                elements = soup.select(pattern)
                if elements:
                    logger.info(f"Found {len(elements)} potential add-to-cart elements with selector '{pattern}'")
                    
                    for element in elements:
                        element_html = str(element)
                        element_text = element.text.strip()
                        
                        logger.info(f"Button text: '{element_text}', HTML snippet: '{element_html[:100]}...'")
                        
                        # Check if button is disabled
                        disabled = ('disabled' in element.get('class', []) or 
                                   element.get('disabled') == 'disabled' or
                                   'disabled' in element_html.lower())
                        
                        if not disabled and ('add to cart' in element_text.lower() or 'buy now' in element_text.lower()):
                            logger.info(f"✅ Product {product_name} is IN STOCK! (Found enabled Add to Cart button)")
                            return True
            
            # DETECTION METHOD 3: Look for any indication of "Out of Stock"
            out_of_stock_indicators = ['out of stock', 'sold out', 'currently unavailable', 'coming soon']
            for indicator in out_of_stock_indicators:
                if indicator in page_text:
                    logger.info(f"❌ Product {product_name} is OUT OF STOCK (found text: '{indicator}')")
                    return False
            
            # DETECTION METHOD 4: Check for price display (usually indicates in stock)
            price_elements = soup.select('.price, .pdp-price, [data-testid="price"]')
            if price_elements:
                # Look for price pattern (₹XX,XXX) to confirm it's actually a price
                for element in price_elements:
                    price_text = element.text.strip()
                    logger.info(f"Found price element with text: '{price_text}'")
                    
                    # Indian Rupee price pattern
                    if re.search(r'₹\s*[\d,]+', price_text):
                        logger.info(f"✅ Product {product_name} shows price, likely IN STOCK")
                        return True
            
            # DETECTION METHOD 5: Delivery availability usually indicates in stock
            delivery_elements = soup.select('.delivery-details, .delivery-info, [data-testid="delivery"]')
            for element in delivery_elements:
                delivery_text = element.text.strip().lower()
                logger.info(f"Found delivery element with text: '{delivery_text}'")
                
                if 'delivery' in delivery_text and not any(x in delivery_text for x in ["unavailable", "not available"]):
                    logger.info(f"✅ Product {product_name} shows delivery options, likely IN STOCK")
                    return True
            
            # If we couldn't definitively determine, check if there are any strong indicators of availability
            if ('add to cart' in page_text and not any(x in page_text for x in out_of_stock_indicators)):
                logger.info(f"✅ Product {product_name} likely IN STOCK (Add to Cart text found without Out of Stock indicators)")
                return True
                
            logger.info(f"⚠️ Couldn't definitively determine stock status for {product_name}, defaulting to OUT OF STOCK")
            return False
            
        else:
            logger.error(f"Failed to load page for {product_name}. Status code: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"Error checking stock for {product_name}: {str(e)}")
        return False

# The rest of the script (main function, etc.) remains the same as before
