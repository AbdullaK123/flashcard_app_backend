from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from schemas import FlashCardPair, FlashCardResponse
from prompts import research_prompt, flashcard_generation_prompt
from utils import logger
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
            model='gpt-4o',
            temperature=0.0
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
    
    def extract_json_from_response(self, content):
        """Extract JSON from LLM response, handling common formatting issues"""
        logger.info(f"LLM response received. Content length: {len(content)}")
        logger.info(f"Response preview: {content[:200]}...")
        
        # Try direct JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.info("Direct JSON parsing failed, trying regex extraction")
            
            # Try regex to extract JSON array
            json_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
            if json_match:
                cards_json = json_match.group(0)
                logger.info(f"JSON match found. Length: {len(cards_json)}")
                return json.loads(cards_json)
            
            # If all fails, raise an exception
            raise ValueError("Failed to extract valid JSON from LLM response")
    
    def conduct_research(self, topic, additional_notes=""):
        """Conduct research on a topic using the agent"""
        logger.info(f"Starting research on topic: {topic}")
        research_result = self.agent_executor.invoke({"topic": topic, "additional_notes": additional_notes})
        research_output = research_result.get("output", "No information found")
        logger.info(f"Research complete. Output length: {len(research_output)}")
        return research_output
    
    def generate_flashcards(self, topic, num_questions):
        """Generate flashcards based on research"""
        # First, research the topic
        research_output = self.conduct_research(topic)
        
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
        
        # Ensure we have exactly the requested number of cards
        if len(cards) > num_questions:
            cards = cards[:num_questions]
            
        # Create flashcard pairs
        flashcard_pairs = [
            FlashCardPair(question=card["question"], answer=card["answer"])
            for card in cards
        ]
        
        logger.info(f"Created {len(flashcard_pairs)} flashcard pairs")
        
        # Return the response
        return FlashCardResponse(
            topic=topic,
            cards=flashcard_pairs,
            source_info="Generated based on web search results"
        )
    
flashcard_service = FlashcardService(
    generation_prompt=flashcard_generation_prompt, 
    research_prompt=research_prompt
)