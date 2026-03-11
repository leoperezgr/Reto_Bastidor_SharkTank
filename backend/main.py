from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Shark Tank Chat API")

# CORS middleware - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== STEP 1: Gemini Configuration =====

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

model_string = GEMINI_MODEL
logger.info(f"Using Gemini API with model: {GEMINI_MODEL}")

# ===== STEP 2: Data Models =====

class Message(BaseModel):
    content: str
    sender: str  # 'Entrepreneur' or 'Judge'

class BusinessIdea(BaseModel):
    name: str
    description: str
    target_market: str
    revenue_model: str
    current_traction: str
    investment_needed: str
    use_of_funds: str

class JudgeAgent(BaseModel):
    name: str
    role: str
    goal: str
    backstory: str

class ChatRequest(BaseModel):
    business_idea: BusinessIdea
    judges: List[JudgeAgent]
    message: Optional[str] = None
    entrepreneur_name: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sender: str
    conversation_history: List[Dict[str, str]]

# ===== STEP 3: Global State =====

conversation_history: List[Dict[str, str]] = []
current_business_idea: Optional[BusinessIdea] = None
judge_agents: List[Agent] = []
current_judges_config: List[Dict[str, str]] = []
entrepreneur_name: str = ""

# ===== STEP 4: Agent Creation Functions =====

def create_llm() -> LLM:
    """Create a Gemini LLM instance for CrewAI"""
    return LLM(
        model=model_string,
        api_key=GEMINI_API_KEY,
    )

def create_judge_agents(judges: List[JudgeAgent]) -> List[Agent]:
    """Create judge agents from the provided configurations"""
    agents = []
    for judge in judges:
        agent = Agent(
            role=judge.role,
            goal=judge.goal,
            backstory=judge.backstory,
            verbose=True,
            allow_delegation=False,
            llm=create_llm(),
        )
        agents.append(agent)
        logger.info(f"Created judge agent: {judge.name}")
    return agents

def create_entrepreneur_agent() -> Agent:
    """Create the entrepreneur agent"""
    return Agent(
        role="Tech Startup Entrepreneur",
        goal="Pitch your innovative business idea and secure investment",
        backstory="""You are a passionate entrepreneur with an innovative tech startup.
        You've developed a revolutionary product and are seeking investment to scale your business.
        You're confident in your product, but you need to convince the Shark Tank judges
        that your business model is sound and that you have a clear path to profitability.
        You understand your market well and have some early traction with customers.""",
        verbose=True,
        allow_delegation=False,
        llm=create_llm(),
    )

# ===== STEP 5: Core Logic Functions =====

def generate_initial_pitch(business_idea: BusinessIdea, entrepreneur_name: str) -> str:
    """Generate initial pitch for the business idea"""
    entrepreneur_agent = create_entrepreneur_agent()

    task = Task(
        description=f"""Create a compelling initial pitch for your business idea.

        Your name is {entrepreneur_name}.

        Your business idea:
        Name: {business_idea.name}
        Description: {business_idea.description}
        Target Market: {business_idea.target_market}
        Revenue Model: {business_idea.revenue_model}
        Current Traction: {business_idea.current_traction}
        Investment Needed: {business_idea.investment_needed}
        Use of Funds: {business_idea.use_of_funds}

        Start your pitch by greeting the judges: "Hello Sharks, I'm {entrepreneur_name}..."

        Be enthusiastic and concise. Highlight the problem you're solving, your solution,
        market opportunity, and why your team is uniquely positioned to succeed.
        End with a clear ask for the investment amount and equity offer.""",
        expected_output="A compelling business pitch for Shark Tank",
        agent=entrepreneur_agent,
    )

    crew = Crew(agents=[entrepreneur_agent], tasks=[task])
    result = crew.kickoff()
    return result.raw


def generate_judge_response(
    business_idea: BusinessIdea, conversation: List[Dict[str, str]]
) -> List[tuple[str, str]]:
    """
    Generate responses from ALL judges.
    Returns: List of (response_text, judge_name) tuples
    """
    if not judge_agents:
        raise HTTPException(status_code=400, detail="No judges configured")

    responses = []
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])

    for idx, judge_agent in enumerate(judge_agents):
        judge_name = (
            current_judges_config[idx]["name"]
            if idx < len(current_judges_config)
            else f"Judge {idx + 1}"
        )

        task = Task(
            description=f"""You are {judge_name}. Evaluate the entrepreneur's pitch and respond appropriately.

            Business being evaluated:
            Name: {business_idea.name}
            Description: {business_idea.description}
            Target Market: {business_idea.target_market}
            Revenue Model: {business_idea.revenue_model}
            Current Traction: {business_idea.current_traction}
            Investment Needed: {business_idea.investment_needed}
            Use of Funds: {business_idea.use_of_funds}

            Conversation history:
            {context}

            Respond with your thoughts, questions or investment decision. Be critical but constructive.
            If you need more information, ask specific questions. If you have enough information,
            make your final investment decision.

            IMPORTANT: Start your response with "{judge_name}: " to identify yourself clearly.""",
            expected_output="Evaluation and feedback on the entrepreneur's pitch",
            agent=judge_agent,
        )

        crew = Crew(agents=[judge_agent], tasks=[task])
        result = crew.kickoff()
        responses.append((result.raw, judge_name))

    return responses


def generate_entrepreneur_response(
    business_idea: BusinessIdea,
    conversation: List[Dict[str, str]],
    user_message: str,
) -> str:
    """Generate entrepreneur's response to judge feedback"""
    entrepreneur_agent = create_entrepreneur_agent()
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])

    task = Task(
        description=f"""Respond to the Shark Tank judge's feedback or questions.

        Your business idea:
        Name: {business_idea.name}
        Description: {business_idea.description}
        Target Market: {business_idea.target_market}
        Revenue Model: {business_idea.revenue_model}
        Current Traction: {business_idea.current_traction}
        Investment Needed: {business_idea.investment_needed}
        Use of Funds: {business_idea.use_of_funds}

        Conversation history:
        {context}

        User's input: {user_message}

        Respond to the judge's feedback or questions thoughtfully.
        Address any concerns they raise, provide additional details about your business when needed,
        and try to convince them of the value of your idea. Be confident but not arrogant.""",
        expected_output="A thoughtful response to the judge's feedback",
        agent=entrepreneur_agent,
    )

    crew = Crew(agents=[entrepreneur_agent], tasks=[task])
    result = crew.kickoff()
    return result.raw

# ===== STEP 6: API Endpoints =====

@app.get("/")
async def root():
    return {"status": "Shark Tank Chat API is running", "model": model_string}


@app.post("/api/test-connection")
async def test_connection():
    """Test Gemini API connection"""
    try:
        test_llm = create_llm()
        test_agent = Agent(
            role="Tester",
            goal="Test API connection",
            backstory="You are a simple agent created to test the API connection.",
            verbose=True,
            llm=test_llm,
        )

        test_task = Task(
            description="Say 'Hello, the connection is working!' and confirm you are using the Gemini API.",
            expected_output="A confirmation message",
            agent=test_agent,
        )

        test_crew = Crew(agents=[test_agent], tasks=[test_task])
        result = test_crew.kickoff()

        return {
            "status": "success",
            "message": "Connection test successful",
            "api": "Gemini",
            "model": model_string,
            "response": result.raw,
        }
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@app.post("/api/start-pitch")
async def start_pitch(request: ChatRequest):
    """Initialize a new pitch session"""
    global conversation_history, current_business_idea, judge_agents, current_judges_config, entrepreneur_name

    try:
        conversation_history = []
        current_business_idea = request.business_idea
        entrepreneur_name = request.entrepreneur_name or "Entrepreneur"
        current_judges_config = [{"name": j.name, "role": j.role} for j in request.judges]
        judge_agents = create_judge_agents(request.judges)

        initial_pitch = generate_initial_pitch(request.business_idea, entrepreneur_name)
        conversation_history.append({
            "role": "Entrepreneur",
            "content": initial_pitch,
            "sender_name": entrepreneur_name,
        })

        judge_responses = generate_judge_response(request.business_idea, conversation_history)
        for judge_response, judge_name in judge_responses:
            conversation_history.append({
                "role": "Judge",
                "content": judge_response,
                "judge_name": judge_name,
            })

        return ChatResponse(
            response=f"Responses from {len(judge_responses)} judge(s)",
            sender="Judge",
            conversation_history=conversation_history,
        )

    except Exception as e:
        logger.error(f"Error starting pitch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting pitch: {str(e)}")


@app.post("/api/send-message")
async def send_message(message: Message):
    """Send a message in the ongoing conversation"""
    global conversation_history, current_business_idea, entrepreneur_name

    if not current_business_idea:
        raise HTTPException(
            status_code=400,
            detail="No active pitch session. Please start a pitch first.",
        )

    try:
        conversation_history.append({
            "role": message.sender,
            "content": message.content,
            "sender_name": entrepreneur_name,
        })

        judge_responses = generate_judge_response(current_business_idea, conversation_history)
        for judge_response, judge_name in judge_responses:
            conversation_history.append({
                "role": "Judge",
                "content": judge_response,
                "judge_name": judge_name,
            })

        return ChatResponse(
            response=f"Responses from {len(judge_responses)} judge(s)",
            sender="Judge",
            conversation_history=conversation_history,
        )

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@app.get("/api/conversation-history")
async def get_conversation_history():
    return {
        "conversation_history": conversation_history,
        "business_idea": current_business_idea.dict() if current_business_idea else None,
    }


@app.post("/api/reset")
async def reset_conversation():
    """Reset the conversation and start fresh"""
    global conversation_history, current_business_idea, judge_agents, current_judges_config, entrepreneur_name

    conversation_history = []
    current_business_idea = None
    judge_agents = []
    current_judges_config = []
    entrepreneur_name = ""

    return {"status": "success", "message": "Conversation reset"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("BACKEND_PORT", 8000)))
