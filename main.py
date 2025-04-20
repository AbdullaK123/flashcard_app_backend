from fastapi import FastAPI
from utils import handle_errors, logger
from services import flashcard_service
from schemas import FlashCardRequest, FlashCardResponse

# Initialize FastAPI app
app = FastAPI(title="Flash Card API")

@app.post('/generate_flashcards', response_model=FlashCardResponse)
@handle_errors
def generate_flashcards(request: FlashCardRequest) -> FlashCardResponse:
    """Endpoint to generate flashcards on a topic"""
    logger.info(f"Received request for topic: {request.topic}, num_questions: {request.num_questions}, additional_notes: {request.additional_notes}")
    return flashcard_service.generate_flashcards(
        request.topic, 
        request.num_questions,
        request.additional_notes
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Flashcard API server...")
    uvicorn.run(app, host='localhost', port=8000)