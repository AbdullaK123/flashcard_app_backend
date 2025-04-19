from langchain_core.prompts import ChatPromptTemplate

flashcard_generation_prompt = ChatPromptTemplate.from_template("""
You are a helpful educational assistant that creates flashcards for studying.

Based on the following context about "{topic}", generate exactly {count} question-answer pairs that would make good flashcards.

Make the questions diverse, covering different aspects of the topic. 
Ensure questions are clear and specific.
Make answers concise but comprehensive enough to be valuable for learning.

IMPORTANT: You MUST respond in valid JSON format ONLY! Your entire response should be a valid JSON array with objects containing "question" and "answer" fields.

CONTEXT:
{context}

INSTRUCTIONS FOR RESPONSE FORMAT:
You must respond ONLY with a valid JSON array. Each element should be an object with "question" and "answer" properties. 
Do not include any text before or after the JSON array.

Example format:
[
  {{"question": "What is the definition of an amphibian?", "answer": "A vertebrate animal capable of living both in water and on land."}},
  {{"question": "What is metamorphosis in amphibians?", "answer": "The transformation process from larval stage to adult form."}}
]

Remember to generate exactly {count} question-answer pairs and ensure your output is valid JSON.
""")

research_prompt = ChatPromptTemplate.from_template("""
You are a research assistant tasked with finding information about {topic}, strictly in service of helping the user
accomplish the following goal and nothing else:

{additional_notes}

Your goal is to gather comprehensive information about this topic that could be used to create educational flashcards.
If it's a technical topic, related to an IT tool, then:
                                                   
Think about:
1. Key definitions and core concepts
2. Best practices when using it
3. The architecture of its internals and how they create implementation nuances
4. How you can help the user deeply understand everything 
5. Potential technical interview questions
                                                   
Otherwise:

Think about:
1. Key definitions and concepts
2. Important facts and figures
3. Historical context if relevant
4. Different perspectives or approaches to the topic
5. Recent developments or current understanding

You have access to the following tools:
{tools}

Use the format:
Thought: I need to find out about...
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know enough to answer the question
Final Answer: the comprehensive information about the topic

{agent_scratchpad}
""")