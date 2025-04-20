from functools import wraps
from fastapi import HTTPException
import logging
import json
import re
from schemas import FlashCardPair, FlashCardResponse

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
            
            # For generate_flashcards endpoint, return a minimal valid response
            if func.__name__ == 'generate_flashcards' and hasattr(args[0], 'topic'):
                request = args[0]
                topic = request.topic
                num_questions = request.num_questions
                
                # Create minimal emergency cards
                emergency_cards = []
                for i in range(min(3, num_questions)):
                    emergency_cards.append(
                        FlashCardPair(
                            question=f"Question {i+1} about {topic}", 
                            answer=f"Information about {topic}. Please try again or refine your search."
                        )
                    )
                
                return FlashCardResponse(
                    topic=topic,
                    cards=emergency_cards,
                    source_info="Generated with limited information due to technical difficulties"
                )
            
            # For other endpoints, raise HTTP exception
            raise HTTPException(
                status_code=500, 
                detail=f"Error: {str(e)}"
            )
    return wrapper

def safe_research(func):
    """Decorator to handle errors in research functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log but continue with empty results
            logger.warning(f"Error during research in {func.__name__}: {str(e)}")
            
            # Get the topic from args if available
            topic = kwargs.get('topic', '')
            if not topic and len(args) > 1:  # self is args[0], topic might be args[1]
                topic = args[1]
                
            # Return a basic fallback
            return f"Basic information about {topic}."
    return wrapper

def safe_json_extraction(func):
    """Decorator to handle JSON extraction errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        content = args[1] if len(args) > 1 else kwargs.get('content', '')
        logger.info(f"Processing LLM response. Content length: {len(content)}")
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Error extracting JSON in {func.__name__}: {str(e)}")
            
            # Try regex to extract JSON array as a fallback
            try:
                json_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
                if json_match:
                    cards_json = json_match.group(0)
                    logger.info(f"JSON match found. Length: {len(cards_json)}")
                    return json.loads(cards_json)
            except Exception:
                logger.warning("Regex extraction also failed")
            
            # Return minimal valid structure if all else fails
            return [{"question": "What is important about this topic?", 
                     "answer": "Please refer to educational resources for detailed information."}]
    return wrapper

def ensure_card_count(func):
    """Decorator to ensure we always return the requested number of cards"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Extract topic and num_questions from arguments
            topic = ''
            num_questions = None  # default
            
            # First try to get from kwargs
            topic = kwargs.get('topic', topic)
            num_questions = kwargs.get('num_questions', num_questions)
            
            # If not in kwargs, try to get from the first argument (request object)
            if hasattr(args[0], 'topic'):
                topic = args[0].topic
            if hasattr(args[0], 'num_questions'):
                num_questions = args[0].num_questions
                
            # Ensure we have the right number of cards
            cards = result.cards if hasattr(result, 'cards') else result
            
            if len(cards) > num_questions:
                cards = cards[:num_questions]
            elif len(cards) < num_questions:
                # Add generic cards if we don't have enough
                for i in range(len(cards), num_questions):
                    cards.append(
                        FlashCardPair(
                            question=f"Additional question #{i+1} about {topic}",
                            answer=f"Further study on {topic} is recommended."
                        ) if hasattr(result, 'cards') else {
                            "question": f"Additional question #{i+1} about {topic}",
                            "answer": f"Further study on {topic} is recommended."
                        }
                    )
            
            # If the result is a FlashCardResponse, update its cards
            if hasattr(result, 'cards'):
                result.cards = cards
                return result
            else:
                # Otherwise just return the cards list
                return cards
            
        except Exception as e:
            logger.error(f"Error in ensure_card_count: {str(e)}")
            return func(*args, **kwargs)  # Fall back to original function
    return wrapper