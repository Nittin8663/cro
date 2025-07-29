import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
from typing import Dict

class CromaProductChecker:
    def __init__(self):
        self.logger = self._setup_logging()
        self.driver = self._setup_webdriver()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('CromaAvailabilityBot')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('availability.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _setup_webdriver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Add a realistic user agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
        return webdriver.Chrome(options=options)

    def check_availability(self, url: str, pincode: str) -> Dict:
        """
        Check product availability for Croma product
        """
        try:
            self.logger.info(f"Checking availability for URL: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Get product name
            try:
                product_name = self.driver.find_element(By.TAG_NAME, "h1").text
            except:
                product_name = "Product Name Not Found"

            # Get price
            try:
                price_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'price')]")
                price = price_element.text.strip()
            except:
                price = "Price Not Found"

            # Check initial availability
            initial_status = self._check_initial_availability()

            # If product appears available, check pincode availability
            if initial_status['is_available']:
                delivery_status = self._check_pincode_availability(pincode)
                initial_status.update(delivery_status)

            # Add product details to response
            result = {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'product_name': product_name,
                'price': price,
                'url': url,
                'pincode': pincode,
                **initial_status
            }

            self.logger.info(f"Check completed: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error checking availability: {str(e)}")
            return {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'is_available': False,
                'url': url,
                'pincode': pincode
            }

    def _check_initial_availability(self) -> Dict:
        """Check basic availability indicators"""
        status = {'is_available': False}

        try:
            # Check for out of stock messages
            out_of_stock_elements = self.driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), 'Out of Stock') or contains(text(), 'Currently Unavailable')]"
            )
            if out_of_stock_elements:
                status['status_message'] = "Out of Stock"
                return status

            # Check for buy now button
            buy_buttons = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), 'Buy Now') or contains(text(), 'ADD TO CART')]"
            )
            if buy_buttons:
                status['is_available'] = True
                status['status_message'] = "Product appears to be in stock"
            else:
                status['status_message'] = "Buy button not found"

        except Exception as e:
            status['status_message'] = f"Error checking initial availability: {str(e)}"

        return status

    def _check_pincode_availability(self, pincode: str) -> Dict:
        """Check delivery availability for pincode"""
        try:
            # Find and fill pincode input
            pincode_input = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text'][@placeholder='Enter Pincode']"))
            )
            pincode_input.clear()
            pincode_input.send_keys(pincode)

            # Click check button
            check_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Check')]")
            check_button.click()

            # Wait and check delivery message
            time.sleep(2)  # Wait for delivery status to update
            
            delivery_messages = self.driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), 'Delivery') or contains(text(), 'delivery')]"
            )
            
            if delivery_messages:
                message = delivery_messages[0].text
                delivery_available = 'not available' not in message.lower()
                return {
                    'delivery_available': delivery_available,
                    'delivery_message': message
                }
            
            return {
                'delivery_available': False,
                'delivery_message': 'Could not find delivery information'
            }

        except Exception as e:
            return {
                'delivery_available': False,
                'delivery_message': f'Error checking delivery: {str(e)}'
            }

    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'driver'):
            self.driver.quit()

# Example usage
if __name__ == "__main__":
    # Initialize checker
    checker = CromaProductChecker()
    
    # Product URL and pincode to check
    url = "https://www.croma.com/vivo-y400-pro-5g-8gb-ram-256gb-freestyle-white-/p/316365"
    pincode = "400049"
    
    # Check availability
    result = checker.check_availability(url, pincode)
    
    # Print results
    print("\nAvailability Check Results:")
    print("=" * 50)
    for key, value in result.items():
        print(f"{key}: {value}")
