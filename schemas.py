from sqlmodel import SQLModel, Field
from pydantic import field_validator
from typing import List, Optional

# Request body schema and response schema
class FlashCardRequest(SQLModel):
    topic: str = Field(..., description="The topic to generate flashcards about")
    num_questions: int = Field(..., description="The number of flashcards to generate")
    additional_notes: str = Field(default="", description="Additional instructions the LLM must follow")

    @field_validator('num_questions')
    def validate_question_count(cls, value):
        if value < 1 or value > 50:
            raise ValueError("num_questions must be an integer between 1 and 50")
        return value
        
class FlashCardPair(SQLModel):
    question: str
    answer: str


class FlashCardResponse(SQLModel):
    topic: str
    cards: List[FlashCardPair]
    source_info: Optional[str] = None