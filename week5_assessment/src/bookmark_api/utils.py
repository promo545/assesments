import logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_audit_log(message: str):
    logger.info(f"AUDIT: {message}")

def send_notification_to_user():
    logger.info("Sent notification to user")
