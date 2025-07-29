import requests
import logging
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger("CromaStockAlert.telegram")

def send_telegram_message(chat_id, message):
    """
    Send a message to a specified Telegram chat
    
    Args:
        chat_id (str): Telegram chat ID to send the message to
        message (str): Message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token is not configured in config.py")
        return False
    
    if not chat_id:
        logger.error("Telegram chat ID is not configured in config.py")
        return False
        
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    
    try:
        logger.debug(f"Sending Telegram message to chat {chat_id}")
        response = requests.post(api_url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        if result.get('ok'):
            logger.info(f"Message sent successfully to Telegram chat {chat_id}")
            return True
        else:
            logger.error(f"Failed to send Telegram message: {result.get('description')}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return False