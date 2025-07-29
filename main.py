#!/usr/bin/env python3
import json
import time
import logging
import os
from datetime import datetime
from stock_checker import check_stock_with_selenium
from telegram_bot import send_telegram_message
from config import TELEGRAM_CHAT_ID, CHECK_INTERVAL

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

def load_products():
    """Load products to monitor from JSON file"""
    try:
        with open('products.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Products file not found. Please create products.json")
        return []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in products.json")
        return []

def main():
    """Main bot function that checks product stock and sends notifications"""
    logger.info("Starting Croma Stock Alert Bot")
    
    # Create directory for screenshots if it doesn't exist
    os.makedirs("screenshots", exist_ok=True)
    
    # Track product stock status to avoid duplicate notifications
    product_status = {}
    
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Running stock check at {current_time}")
        
        products = load_products()
        if not products:
            logger.warning("No products found to monitor. Add products to products.json")
            time.sleep(CHECK_INTERVAL)
            continue
        
        for product in products:
            product_id = product['id']
            name = product['name']
            url = product['url']
            
            try:
                in_stock = check_stock_with_selenium(url, name)
                
                # If product is now in stock but wasn't before (or we're checking it for the first time)
                if in_stock and product_status.get(product_id) != True:
                    product_status[product_id] = True
                    message = f"🎉 IN STOCK ALERT! 🎉\n\n{name} is now available at Croma!\n\nYou can buy it here: {url}\n\nChecked at: {current_time}"
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    logger.info(f"Product now in stock, notification sent: {name}")
                
                # If product was in stock before but isn't anymore
                elif not in_stock and product_status.get(product_id) == True:
                    product_status[product_id] = False
                    message = f"⚠️ OUT OF STOCK ALERT ⚠️\n\n{name} is no longer available at Croma.\n\nWe'll notify you when it's back in stock."
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    logger.info(f"Product now out of stock: {name}")
                
                # No change in status, just log it
                else:
                    status_text = "in stock" if in_stock else "out of stock"
                    product_status[product_id] = in_stock
                    logger.info(f"Product {name} remains {status_text}")
                    
            except Exception as e:
                logger.error(f"Error checking product {name}: {str(e)}")
        
        logger.info(f"Finished checking all products. Next check in {CHECK_INTERVAL} seconds.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
