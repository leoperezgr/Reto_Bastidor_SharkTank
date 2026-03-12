from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
import logging

from judges_config import MODES, ModeConfig

# Load environment variables from the same directory as this script
load_dotenv(Path(__file__).resolve().parent / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Shark Tank Chat API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Gemini Configuration =====

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-1.5-pro")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
logger.info(f"Using Gemini API with model: {GEMINI_MODEL}")


# ===== Data Models (aligned with Unity frontend) =====


class BusinessIdeaData(BaseModel):
    name: str
    description: str
    target_market: str
    revenue_model: str
    current_traction: str
    investment_needed: str
    use_of_funds: str


class JudgeDefinition(BaseModel):
    id: str
    name: str
    role: str
    goal: str
    backstory: str


class StartSessionRequest(BaseModel):
    entrepreneur_name: str
    mode: str
    business_idea: BusinessIdeaData
    judges: List[JudgeDefinition]


class NextTurnRequest(BaseModel):
    session_id: str
    user_message: str


class AgentMessage(BaseModel):
    message_id: str
    agent_id: str
    agent_name: str
    agent_role: str
    text: str
    emotion: str = "neutral"
    animation: str = "idle"
    ui_target: str = "panel"
    timestamp: str = ""


class UiHints(BaseModel):
    layout: str = "panel"
    show_typing_effect: bool = True
    auto_advance: bool = False


class SessionTurnResponse(BaseModel):
    session_id: str
    turn: int
    scene: str
    messages: List[AgentMessage]
    ui_hints: UiHints
    conversation_status: str


# ===== Session Storage =====


class Session:
    def __init__(
        self,
        session_id: str,
        business_idea: BusinessIdeaData,
        judges: List[JudgeDefinition],
        entrepreneur_name: str,
        mode_config: ModeConfig,
    ):
        self.session_id = session_id
        self.business_idea = business_idea
        self.judges = judges
        self.entrepreneur_name = entrepreneur_name
        self.mode = mode_config
        self.turn = 0
        self.judge_round = 0  # how many judge rounds have been executed
        self.conversation: List[Dict[str, str]] = []
        self.judge_agents: List[Agent] = []
        self.last_round_responses: List[Dict] = []  # for panel_debate


sessions: Dict[str, Session] = {}


# ===== Helpers =====


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _msg_id() -> str:
    return uuid.uuid4().hex[:12]


def create_llm() -> LLM:
    return LLM(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)


def create_judge_agents(judges: List[JudgeDefinition]) -> List[Agent]:
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


def format_idea(idea: BusinessIdeaData) -> str:
    return (
        f"Startup: {idea.name}\n"
        f"Description: {idea.description}\n"
        f"Target Market: {idea.target_market}\n"
        f"Revenue Model: {idea.revenue_model}\n"
        f"Current Traction: {idea.current_traction}\n"
        f"Investment Needed: {idea.investment_needed}\n"
        f"Use of Funds: {idea.use_of_funds}"
    )


def build_judge_prompt(
    judge: JudgeDefinition,
    idea_str: str,
    entrepreneur_name: str,
    conversation: List[Dict[str, str]],
    mode: ModeConfig,
    round_number: int,
    total_rounds: int,
    peer_responses: Optional[List[Dict]] = None,
) -> str:
    """Build a mode-aware, round-aware prompt for a judge agent."""

    history = ""
    if conversation:
        history = "\n\nConversation so far:\n" + "\n".join(
            f"{m['role']}: {m['content']}" for m in conversation
        )

    debate = ""
    if peer_responses and mode.group_debate:
        others = [r for r in peer_responses if r["judge_id"] != judge.id]
        if others:
            debate = "\n\nWhat your fellow judges have said:\n" + "\n".join(
                f"{r['judge_name']}: {r['content']}" for r in others
            )

    round_ctx = ""
    if total_rounds > 1:
        round_ctx = f"\nThis is round {round_number} of {total_rounds}."

    return (
        f"You are {judge.name}, a {judge.role}.\n\n"
        f"The entrepreneur {entrepreneur_name} is pitching the following business:\n\n"
        f"{idea_str}{history}{debate}{round_ctx}\n\n"
        f"{mode.judge_instruction}\n\n"
        "IMPORTANT: Do NOT start your response with your name. Just give your response directly."
    )


# ===== Core Logic =====


def generate_initial_pitch(session: Session) -> str:
    """Generate the entrepreneur's opening pitch."""
    idea = session.business_idea
    entrepreneur_agent = Agent(
        role="Tech Startup Entrepreneur",
        goal="Pitch your innovative business idea and secure investment",
        backstory=(
            "You are a passionate entrepreneur with an innovative tech startup. "
            "You've developed a revolutionary product and are seeking investment to scale."
        ),
        verbose=True,
        allow_delegation=False,
        llm=create_llm(),
    )

    task = Task(
        description=f"""Create a compelling initial pitch for your business idea.

        Your name is {session.entrepreneur_name}.

        Your business idea:
        {format_idea(idea)}

        Start your pitch by greeting the judges: "Hello Sharks, I'm {session.entrepreneur_name}..."

        Be enthusiastic and concise. Highlight the problem you're solving, your solution,
        market opportunity, and why your team is uniquely positioned to succeed.
        End with a clear ask for the investment amount.""",
        expected_output="A compelling business pitch for Shark Tank",
        agent=entrepreneur_agent,
    )

    crew = Crew(agents=[entrepreneur_agent], tasks=[task])
    return crew.kickoff().raw.strip()


def run_judge_round(session: Session) -> List[AgentMessage]:
    """Execute one round of judge responses, using mode-aware prompts."""
    session.judge_round += 1
    idea_str = format_idea(session.business_idea)
    total_rounds = session.mode.total_rounds or 1
    messages: List[AgentMessage] = []
    round_responses: List[Dict] = []

    for idx, judge_agent in enumerate(session.judge_agents):
        judge = session.judges[idx]

        prompt = build_judge_prompt(
            judge=judge,
            idea_str=idea_str,
            entrepreneur_name=session.entrepreneur_name,
            conversation=session.conversation,
            mode=session.mode,
            round_number=session.judge_round,
            total_rounds=total_rounds,
            peer_responses=session.last_round_responses if session.mode.group_debate else None,
        )

        task = Task(
            description=prompt,
            expected_output="Judge's response to the entrepreneur",
            agent=judge_agent,
        )
        crew = Crew(agents=[judge_agent], tasks=[task])
        response_text = crew.kickoff().raw.strip()

        # Strip judge name prefix if added by LLM
        prefix = f"{judge.name}: "
        if response_text.startswith(prefix):
            response_text = response_text[len(prefix):]

        round_responses.append({
            "judge_id": judge.id,
            "judge_name": judge.name,
            "content": response_text,
        })

        session.conversation.append(
            {"role": judge.name, "content": response_text}
        )

        messages.append(AgentMessage(
            message_id=_msg_id(),
            agent_id=judge.id,
            agent_name=judge.name,
            agent_role=judge.role,
            text=response_text,
            timestamp=_now(),
        ))

    session.last_round_responses = round_responses
    return messages


def determine_scene_and_status(session: Session) -> tuple[str, str]:
    """Determine the current scene label and whether the session is complete."""
    mode = session.mode
    jr = session.judge_round  # how many judge rounds have been executed

    if mode.id == "quick":
        # 1 round total (the start round is the verdict)
        return "verdict", "complete"

    if mode.id == "rapid_fire":
        if jr <= 1:
            return "qa", "awaiting_response"
        else:
            return "verdict", "complete"

    if mode.id == "panel_debate":
        if jr <= 1:
            return "qa", "awaiting_response"
        # After entrepreneur answers round 1, we run debate + verdict
        # back-to-back (rounds 2 & 3), so when jr >= 3 we're done
        if jr >= 3:
            return "verdict", "complete"
        return "debate", "awaiting_response"

    # normal & full_tank
    is_last_qa = jr >= mode.qa_rounds
    if is_last_qa and not mode.allow_negotiation:
        return "verdict", "complete"
    if is_last_qa and mode.allow_negotiation:
        return "negotiation", "awaiting_response"
    if jr > mode.qa_rounds:
        # negotiation round done
        return "negotiation", "complete"
    return "qa", "awaiting_response"


# ===== API Endpoints =====


@app.get("/")
async def root():
    return {"status": "Shark Tank Chat API is running", "model": GEMINI_MODEL}


@app.get("/api/modes")
async def list_modes():
    """Return available simulation modes so the frontend can display them."""
    return {
        mid: {
            "name": m.name,
            "icon": m.icon,
            "description": m.description,
            "qa_rounds": m.qa_rounds,
            "allow_negotiation": m.allow_negotiation,
            "group_debate": m.group_debate,
        }
        for mid, m in MODES.items()
    }


@app.post("/api/session/start", response_model=SessionTurnResponse)
async def start_session(request: StartSessionRequest):
    """Initialize a new pitch session and return the first turn."""
    mode_config = MODES.get(request.mode)
    if not mode_config:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mode '{request.mode}'. Available: {list(MODES.keys())}",
        )

    try:
        session_id = uuid.uuid4().hex[:16]
        session = Session(
            session_id=session_id,
            business_idea=request.business_idea,
            judges=request.judges,
            entrepreneur_name=request.entrepreneur_name,
            mode_config=mode_config,
        )
        session.judge_agents = create_judge_agents(request.judges)
        sessions[session_id] = session

        # --- Entrepreneur pitch ---
        pitch = generate_initial_pitch(session)
        session.conversation.append({"role": "Entrepreneur", "content": pitch})

        entrepreneur_msg = AgentMessage(
            message_id=_msg_id(),
            agent_id="entrepreneur",
            agent_name=session.entrepreneur_name,
            agent_role="Entrepreneur",
            text=pitch,
            timestamp=_now(),
        )

        # --- First judge round ---
        judge_messages = run_judge_round(session)

        session.turn = 1
        scene, status = determine_scene_and_status(session)

        return SessionTurnResponse(
            session_id=session_id,
            turn=session.turn,
            scene=scene,
            messages=[entrepreneur_msg] + judge_messages,
            ui_hints=UiHints(
                layout="panel",
                show_typing_effect=True,
                auto_advance=(status == "complete"),
            ),
            conversation_status=status,
        )

    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")


@app.post("/api/session/next-turn", response_model=SessionTurnResponse)
async def next_turn(request: NextTurnRequest):
    """Process the entrepreneur's reply and return judge responses."""
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Don't accept turns on completed sessions
    _, current_status = determine_scene_and_status(session)
    if current_status == "complete":
        raise HTTPException(status_code=400, detail="Session is already complete")

    try:
        # --- Add entrepreneur message ---
        session.conversation.append(
            {"role": "Entrepreneur", "content": request.user_message}
        )

        entrepreneur_msg = AgentMessage(
            message_id=_msg_id(),
            agent_id="entrepreneur",
            agent_name=session.entrepreneur_name,
            agent_role="Entrepreneur",
            text=request.user_message,
            timestamp=_now(),
        )

        all_messages = [entrepreneur_msg]

        # --- Run judge round(s) ---
        # For panel_debate after the entrepreneur answers round 1,
        # we run both the debate round and the verdict round back-to-back
        if session.mode.id == "panel_debate" and session.judge_round == 1:
            # Round 2: debate
            debate_messages = run_judge_round(session)
            all_messages.extend(debate_messages)
            # Round 3: final verdict
            verdict_messages = run_judge_round(session)
            all_messages.extend(verdict_messages)
        else:
            judge_messages = run_judge_round(session)
            all_messages.extend(judge_messages)

        session.turn += 1
        scene, status = determine_scene_and_status(session)

        return SessionTurnResponse(
            session_id=session.session_id,
            turn=session.turn,
            scene=scene,
            messages=all_messages,
            ui_hints=UiHints(
                layout="panel",
                show_typing_effect=True,
                auto_advance=(status == "complete"),
            ),
            conversation_status=status,
        )

    except Exception as e:
        logger.error(f"Error processing turn: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing turn: {str(e)}")


@app.post("/api/test-connection")
async def test_connection():
    """Test Gemini API connection."""
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
            "model": GEMINI_MODEL,
            "response": result.raw,
        }
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@app.post("/api/reset")
async def reset_session(session_id: Optional[str] = None):
    """Reset a specific session or all sessions."""
    if session_id:
        sessions.pop(session_id, None)
        return {"status": "success", "message": f"Session {session_id} reset"}
    else:
        sessions.clear()
        return {"status": "success", "message": "All sessions reset"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("BACKEND_PORT", 8000)))
