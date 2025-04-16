from functools import wraps
from fastapi import HTTPException
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("flashcard-app")

def handle_errors(func):
    """Decorator to catch and convert exceptions to HTTP responses"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in function {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Error generating flashcards: {str(e)}"
            )
    return wrapper