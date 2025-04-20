from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from schemas import FlashCardPair, FlashCardResponse
from prompts import research_prompt, flashcard_generation_prompt
from utils import logger, safe_research, safe_json_extraction, ensure_card_count
import json
import re
from dotenv import load_dotenv

load_dotenv()

class FlashcardService:
    """Service class to handle flashcard generation logic"""
    
    def __init__(self, generation_prompt: ChatPromptTemplate, research_prompt: ChatPromptTemplate):
        # Init the search tool
        self.search_tool = DuckDuckGoSearchRun()
        
        # Set up tools and reasoning engine
        self.tools = [
            Tool(
                name="Web Search",
                func=self.search_tool.run,
                description="Useful for searching the web for information about a specific topic"
            ),
            Tool(
                name="Length of an array",
                func=len,
                description="A helpful tool to calculate the length of an array"
            )
        ]
        
        self.llm = ChatOpenAI(
            model='o3-mini-2025-01-31'
        )
        
        # Set up prompts
        self.flashcard_generation_prompt = generation_prompt
        
        self.research_prompt = research_prompt
        
        # Set up agent
        self.research_agent = create_react_agent(self.llm, self.tools, self.research_prompt)
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.research_agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
    @safe_json_extraction
    def extract_json_from_response(self, content):
        """Extract JSON from LLM response"""
        # Direct JSON parsing - safe_json_extraction decorator handles errors
        return json.loads(content) 
    
    @safe_research
    def conduct_research(self, topic, additional_notes=""):
        """Conduct research on a topic using the agent"""
        logger.info(f"Starting research on topic: {topic}")
        research_result = self.agent_executor.invoke({"topic": topic, "additional_notes": additional_notes})
        research_output = research_result.get("output", "")
        logger.info(f"Research complete. Output length: {len(research_output)}")
        return research_output
    
    @ensure_card_count
    def generate_flashcards(self, topic, num_questions, additional_notes=""):
        """Generate flashcards based on research"""
        # First, research the topic
        research_output = self.conduct_research(topic, additional_notes)
        
        # Generate flashcards using the research output
        logger.info("Generating flashcards...")
        flashcard_result = self.llm.invoke(
            self.flashcard_generation_prompt.format(
                topic=topic,
                context=research_output,
                count=num_questions
            )
        )
        
        # Extract and process the cards
        cards = self.extract_json_from_response(flashcard_result.content)
        
        # Create flashcard pairs - ensure_card_count decorator handles missing cards
        flashcard_pairs = [
            FlashCardPair(question=card["question"], answer=card["answer"])
            for card in cards
        ]
        
        logger.info(f"Created {len(flashcard_pairs)} flashcard pairs")
        
        # Return the response
        return FlashCardResponse(
            topic=topic,
            cards=flashcard_pairs,
            source_info="Generated based on available information"
        )
    
flashcard_service = FlashcardService(
    generation_prompt=flashcard_generation_prompt, 
    research_prompt=research_prompt
)