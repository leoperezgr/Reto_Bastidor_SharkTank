#!/usr/bin/env python3
"""
Shark Tank AI — Console Demo
Interactive Shark Tank simulation powered by Gemini + CrewAI
"""

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from dotenv import load_dotenv

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from crewai import Agent, Crew, LLM, Task

from judges_config import JUDGES, MODES, JudgeProfile, ModeConfig

# ---------------------------------------------------------------------------
# Demo defaults
# ---------------------------------------------------------------------------

DEMO_IDEA: Dict[str, str] = {
    "entrepreneur_name": "Equipo Bastidor",
    "name": "SharkLab AI",
    "tagline": "Convierte nervios en preparación, y preparación en inversión.",
    "problem": (
        "Miles de estudiantes presentan ideas brillantes que fracasan no por falta de "
        "potencial, sino por una mala presentación ante inversionistas. El problema no "
        "es la idea. Es la preparación."
    ),
    "solution": (
        "Simulador multiagente que recrea un panel de inversionistas con distintas "
        "personalidades: un financiero conservador, un visionario tecnológico, un "
        "pragmático operativo y un estratega de mercado. El usuario presenta su pitch y "
        "enfrenta preguntas reales, debate crítico y una decisión final de inversión, "
        "todo en un entorno seguro pero exigente. Lo innovador: los agentes debaten entre "
        "ellos, generando dinámicas emergentes similares a un panel real de Shark Tank. "
        "Al finalizar, el emprendedor recibe métricas claras, riesgos detectados y "
        "recomendaciones accionables para mejorar."
    ),
    "target_market": (
        "Universidades e incubadoras que buscan elevar la calidad de sus proyectos antes "
        "de presentarlos a fondos reales."
    ),
    "revenue_model": "SaaS institucional — licencias para universidades e incubadoras",
    "current_traction": "MVP funcional con simulador multiagente en producción",
    "investment_needed": "$150,000",
    "equity_offered": "10%",
    "use_of_funds": (
        "Desarrollo de producto, adquisición de primeros clientes institucionales y "
        "expansión de mercado latinoamericano."
    ),
}

DEMO_JUDGE_IDS = ["the_shark", "the_disruptor", "the_oracle", "the_perfectionist"]
DEMO_MODE_ID = "quick"

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

load_dotenv()

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-1.5-pro")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not set. Create a .env file with your key.")
    sys.exit(1)

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

console = Console()
_llm = LLM(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def risk_bar(appetite: int) -> str:
    return "█" * appetite + "░" * (10 - appetite)


def risk_color(appetite: int) -> str:
    return "green" if appetite >= 7 else "yellow" if appetite >= 4 else "red"


def run_judge_task(judge: JudgeProfile, prompt: str) -> str:
    agent = Agent(
        role=judge.role,
        goal=judge.goal,
        backstory=judge.backstory,
        verbose=False,
        allow_delegation=False,
        llm=_llm,
    )
    task = Task(
        description=prompt,
        expected_output="Judge's response to the entrepreneur",
        agent=agent,
    )
    return Crew(agents=[agent], tasks=[task]).kickoff().raw.strip()


def run_judge_round(
    judges: List[JudgeProfile],
    build_prompt: Callable[[JudgeProfile], str],
    label: str = "",
    spinner: str = "Panel deliberating…",
) -> List[Dict]:
    """Run all judges in parallel, print their panels, return responses."""

    def call(judge: JudgeProfile) -> Dict:
        return {
            "judge_id": judge.id,
            "judge_name": judge.name,
            "content": run_judge_task(judge, build_prompt(judge)),
        }

    with Progress(
        SpinnerColumn(style="bold cyan"),
        TextColumn(f"[bold cyan]{spinner}[/bold cyan]"),
        transient=True,
        console=console,
    ) as p:
        p.add_task("", total=None)
        with ThreadPoolExecutor(max_workers=len(judges)) as ex:
            results = {r["judge_id"]: r for r in ex.map(call, judges)}

    responses = []
    for judge in judges:
        r = results[judge.id]
        responses.append(r)
        console.print(judge_panel(judge, r["content"], label=label))
        console.print()
    return responses


def judge_panel(judge: JudgeProfile, content: str, label: str = "") -> Panel:
    header = f"[bold {judge.color}]{judge.icon}  {judge.name}[/bold {judge.color}]"
    subtitle = f"[dim]{judge.title}[/dim]" + (
        f"  [bold]{label}[/bold]" if label else ""
    )
    return Panel(
        content,
        title=header,
        subtitle=subtitle,
        border_style=judge.color,
        padding=(1, 2),
    )


def verdict_badge(text: str) -> str:
    t = text.upper()
    if re.search(r"VERDICT:\s*INVEST", t):
        return "[bold green]✅ INVEST[/bold green]"
    if re.search(r"VERDICT:\s*PASS", t):
        return "[bold red]❌  PASS[/bold red]"
    return "[bold yellow]🤔 UNDECIDED[/bold yellow]"


def show_pitch_panel(idea: Dict[str, str]) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold]{idea['entrepreneur_name']}[/bold] pitches [bold cyan]{idea['name']}[/bold cyan]\n\n"
            f"[italic]\"{idea['tagline']}\"[/italic]\n\n{format_idea(idea)}",
            title="[bold green]🎤  The Pitch[/bold green]",
            border_style="green",
        )
    )


def format_idea(idea: Dict[str, str]) -> str:
    return (
        f"Startup: {idea['name']}\n"
        f"Tagline: {idea['tagline']}\n"
        f"Problem: {idea['problem']}\n"
        f"Solution: {idea['solution']}\n"
        f"Target Market: {idea['target_market']}\n"
        f"Revenue Model: {idea['revenue_model']}\n"
        f"Current Traction: {idea['current_traction']}\n"
        f"Investment Ask: {idea['investment_needed']} for {idea['equity_offered']} equity\n"
        f"Use of Funds: {idea['use_of_funds']}"
    )


def build_judge_prompt(
    judge: JudgeProfile,
    idea_str: str,
    entrepreneur_name: str,
    conversation: List[Dict],
    mode: ModeConfig,
    round_number: int,
    total_rounds: int,
    peer_responses: Optional[List[Dict]] = None,
) -> str:
    history = (
        "\n\nConversation so far:\n"
        + "\n".join(f"{m['role']}: {m['content']}" for m in conversation)
        if conversation
        else ""
    )
    debate = ""
    if peer_responses and mode.group_debate:
        others = [r for r in peer_responses if r["judge_id"] != judge.id]
        if others:
            debate = "\n\nWhat your fellow judges have said:\n" + "\n".join(
                f"{r['judge_name']}: {r['content']}" for r in others
            )
    round_ctx = (
        f"\nThis is round {round_number} of {total_rounds}." if total_rounds > 1 else ""
    )

    return (
        f"You are {judge.name}, {judge.title}.\n\n"
        f"The entrepreneur {entrepreneur_name} is pitching the following business:\n\n"
        f"{idea_str}{history}{debate}{round_ctx}\n\n"
        f"{mode.judge_instruction}\n\n"
        f'IMPORTANT: Begin your response with "{judge.name}: " to identify yourself.'
    )


# ---------------------------------------------------------------------------
# UI screens
# ---------------------------------------------------------------------------

BANNER = r"""
  _____ _                _      _____              _
 / ____| |              | |    |_   _|            | |
| (___ | |__   __ _ _ __| | __   | |   __ _ _ __ | | __
 \___ \| '_ \ / _` | '__| |/ /   | |  / _` | '_ \| |/ /
 ____) | | | | (_| | |  |   <   _| |_| (_| | | | |   <
|_____/|_| |_|\__,_|_|  |_|\_\ |_____|\__,_|_| |_|_|\_\
"""


def show_welcome():
    console.print()
    console.print(
        Panel(
            Align.center(
                Text(BANNER, style="bold cyan")
                + Text("\n  Equipo Bastidor\n", style="dim")
            ),
            border_style="cyan",
            box=box.DOUBLE_EDGE,
        )
    )
    console.print()


def show_judge_table():
    table = Table(
        title="[bold]Available Judges[/bold]",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Judge", min_width=22)
    table.add_column("Type", width=8)
    table.add_column("Focus Areas", min_width=30)
    table.add_column("Risk", justify="center", width=6)
    table.add_column("Equity", width=10)
    table.add_column("Deal Range", width=16)

    for i, (_, j) in enumerate(JUDGES.items(), 1):
        bar = risk_bar(j.risk_appetite)
        color = risk_color(j.risk_appetite)
        table.add_row(
            str(i),
            f"[bold {j.color}]{j.icon} {j.name}[/bold {j.color}]\n[dim]{j.title}[/dim]",
            (
                "[dim italic]Real[/dim italic]"
                if j.inspired_by
                else "[dim]Archetype[/dim]"
            ),
            "\n".join(f"• {f}" for f in j.focus_areas[:3]),
            f"[{color}]{bar[:5]}[/{color}]",
            j.typical_equity,
            j.deal_range,
        )
    console.print(table)
    console.print()


def select_judges() -> List[JudgeProfile]:
    judge_list = list(JUDGES.values())
    while True:
        raw = Prompt.ask(
            "[bold cyan]Select judges[/bold cyan] [dim](comma-separated numbers, e.g. 1,3,7  or 'all')[/dim]"
        )
        if raw.strip().lower() == "all":
            return judge_list
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            selected = [judge_list[i] for i in indices]
            if selected:
                return selected
        except (ValueError, IndexError):
            pass
        console.print(
            "[red]Invalid selection — please enter valid numbers from the table.[/red]"
        )


def show_mode_table():
    table = Table(
        title="[bold]Simulation Modes[/bold]",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Mode", min_width=18)
    table.add_column("Description", min_width=50)
    table.add_column("Rounds", justify="center", width=7)
    table.add_column("Negotiation", justify="center", width=12)

    for i, (_, m) in enumerate(MODES.items(), 1):
        table.add_row(
            str(i),
            f"{m.icon} [bold]{m.name}[/bold]",
            m.description,
            str(m.qa_rounds) if m.qa_rounds else "1",
            "✅" if m.allow_negotiation else "—",
        )
    console.print(table)
    console.print()


def select_mode() -> ModeConfig:
    mode_list = list(MODES.values())
    while True:
        raw = Prompt.ask(
            "[bold cyan]Choose a mode[/bold cyan] [dim](enter number)[/dim]"
        )
        try:
            idx = int(raw.strip()) - 1
            if 0 <= idx < len(mode_list):
                return mode_list[idx]
        except ValueError:
            pass
        console.print("[red]Invalid selection.[/red]")


def collect_business_idea() -> Dict[str, str]:
    console.print()
    console.rule("[bold cyan]Your Business Idea[/bold cyan]")
    console.print("[dim]Answer each question — press Enter to move on.[/dim]\n")

    fields = [
        ("entrepreneur_name", "Your name"),
        ("name", "Startup name"),
        ("tagline", "One-sentence tagline"),
        ("problem", "Problem you're solving"),
        ("solution", "Your solution / product"),
        ("target_market", "Target market (who & how many)"),
        ("revenue_model", "Revenue model"),
        ("current_traction", "Current traction (users / revenue / key milestones)"),
        ("investment_needed", "How much are you asking for?"),
        ("equity_offered", "Equity you're offering (%)"),
        ("use_of_funds", "What will you do with the funds?"),
    ]

    idea: Dict[str, str] = {}
    for key, label in fields:
        idea[key] = Prompt.ask(f"  [bold]{label}[/bold]").strip() or "Not specified"
    return idea


def show_selected_summary(judges: List[JudgeProfile], mode: ModeConfig):
    cols = [
        Panel(
            f"[bold {j.color}]{j.icon}  {j.name}[/bold {j.color}]\n"
            f"[dim]{j.title}[/dim]\n"
            f"Risk: {risk_bar(j.risk_appetite)}  {j.risk_appetite}/10\n"
            f'[italic]"{j.catchphrase}"[/italic]',
            border_style=j.color,
            padding=(0, 1),
        )
        for j in judges
    ]
    console.print()
    console.rule("[bold]Your Panel[/bold]")
    console.print(Columns(cols, equal=True, expand=True))
    console.print()
    console.print(
        Panel(
            f"{mode.icon}  [bold]{mode.name}[/bold]  —  {mode.description}",
            title="[bold]Mode[/bold]",
            border_style="cyan",
        )
    )
    console.print()


def show_verdict_summary(judges: List[JudgeProfile], responses: List[Dict], idea: Dict):
    console.print()
    console.rule("[bold cyan]Final Verdicts[/bold cyan]")

    table = Table(
        box=box.ROUNDED, header_style="bold cyan", show_lines=True, expand=True
    )
    table.add_column("Judge", min_width=20)
    table.add_column("Verdict", justify="center", width=16)
    table.add_column("Key Concern / Comment", min_width=45)

    for j in judges:
        r = next((r for r in responses if r["judge_id"] == j.id), None)
        if not r:
            continue
        snippet = r["content"][:160].replace("\n", " ") + (
            "…" if len(r["content"]) > 160 else ""
        )
        table.add_row(
            f"[bold {j.color}]{j.icon} {j.name}[/bold {j.color}]",
            verdict_badge(r["content"]),
            snippet,
        )

    console.print(table)
    console.print()
    console.print(
        Panel(
            f"[bold]Pitch:[/bold] {idea['name']}  ·  "
            f"[bold]Ask:[/bold] {idea['investment_needed']} for {idea['equity_offered']}  ·  "
            f"[bold]Pitcher:[/bold] {idea['entrepreneur_name']}",
            title="[bold cyan]Session Summary[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------


def run_quick_or_rapid(judges: List[JudgeProfile], mode: ModeConfig, idea: Dict):
    idea_str = format_idea(idea)
    entrepreneur_name = idea["entrepreneur_name"]

    console.print()
    console.rule(f"[bold cyan]{mode.icon}  {mode.name.upper()}[/bold cyan]")
    show_pitch_panel(idea)
    console.print()

    conversation: List[Dict] = [{"role": "Entrepreneur", "content": idea_str}]

    def prompt(judge):
        return build_judge_prompt(
            judge, idea_str, entrepreneur_name, conversation, mode, 1, 1
        )

    responses = run_judge_round(judges, prompt)

    if mode.id == "rapid_fire":
        console.print()
        console.rule("[bold yellow]🔥  Your Turn — Answer Everything[/bold yellow]")
        all_questions = "\n\n".join(
            f"[bold {j.color}]{j.name}:[/bold {j.color}] {r['content']}"
            for j, r in zip(judges, responses)
        )
        console.print(
            Panel(
                all_questions, title="Questions from the panel", border_style="yellow"
            )
        )
        console.print()
        answer = Prompt.ask(
            "[bold green]Your response (address all questions)[/bold green]"
        )
        conversation.extend(responses)
        conversation.append({"role": "Entrepreneur", "content": answer})

        def prompt2(judge):
            return build_judge_prompt(
                judge, idea_str, entrepreneur_name, conversation, mode, 2, 2
            )

        responses = run_judge_round(
            judges, prompt2, label="VERDICT", spinner="Panel delivering verdicts…"
        )

    show_verdict_summary(judges, responses, idea)


def run_normal_or_full_tank(judges: List[JudgeProfile], mode: ModeConfig, idea: Dict):
    idea_str = format_idea(idea)
    entrepreneur_name = idea["entrepreneur_name"]

    console.print()
    console.rule(f"[bold cyan]{mode.icon}  {mode.name.upper()}[/bold cyan]")
    show_pitch_panel(idea)

    conversation: List[Dict] = [{"role": "Entrepreneur", "content": idea_str}]
    final_responses: List[Dict] = []
    total = mode.total_rounds

    for round_num in range(1, mode.qa_rounds + 1):
        is_last = round_num == mode.qa_rounds
        round_label = (
            "Final Verdicts"
            if is_last and not mode.allow_negotiation
            else f"Round {round_num}"
        )
        console.print()
        console.rule(
            f"[bold yellow]{'🔔' if is_last else '💬'}  {round_label}[/bold yellow]"
        )
        console.print()

        label = "VERDICT" if is_last else f"Round {round_num}"
        rn, tot = round_num, total

        def prompt(judge, _rn=rn, _tot=tot):
            return build_judge_prompt(
                judge, idea_str, entrepreneur_name, conversation, mode, _rn, _tot
            )

        round_responses = run_judge_round(judges, prompt, label=label)
        conversation.extend(
            {"role": r["judge_name"], "content": r["content"]} for r in round_responses
        )
        final_responses = round_responses

        if not (is_last and not mode.allow_negotiation):
            console.print()
            console.rule("[bold green]Your Turn[/bold green]")
            answer = Prompt.ask(f"[bold green]{entrepreneur_name}[/bold green]")
            conversation.append({"role": "Entrepreneur", "content": answer})

    if mode.allow_negotiation:
        console.print()
        console.rule("[bold magenta]🤝  Negotiation[/bold magenta]")

        def neg_prompt(judge):
            return build_judge_prompt(
                judge, idea_str, entrepreneur_name, conversation, mode, total, total
            )

        neg_responses = run_judge_round(
            judges,
            neg_prompt,
            label="OFFER / WALK",
            spinner="Judges making their moves…",
        )
        conversation.extend(
            {"role": r["judge_name"], "content": r["content"]} for r in neg_responses
        )
        final_responses = neg_responses

        console.print()
        console.rule("[bold green]Final Response[/bold green]")
        answer = Prompt.ask(
            f"[bold green]{entrepreneur_name} (accept / counter / decline)[/bold green]"
        )
        conversation.append({"role": "Entrepreneur", "content": answer})

    show_verdict_summary(judges, final_responses, idea)


def run_panel_debate(judges: List[JudgeProfile], mode: ModeConfig, idea: Dict):
    idea_str = format_idea(idea)
    entrepreneur_name = idea["entrepreneur_name"]

    console.print()
    console.rule(f"[bold cyan]{mode.icon}  PANEL DEBATE[/bold cyan]")
    show_pitch_panel(idea)

    conversation: List[Dict] = [{"role": "Entrepreneur", "content": idea_str}]

    # Round 1: Initial reactions
    console.print()
    console.rule("[bold yellow]💬  Initial Reactions[/bold yellow]")
    console.print()

    def r1_prompt(judge):
        return build_judge_prompt(
            judge, idea_str, entrepreneur_name, conversation, mode, 1, 3
        )

    round1 = run_judge_round(judges, r1_prompt, label="Round 1")
    conversation.extend(
        {"role": r["judge_name"], "content": r["content"]} for r in round1
    )

    console.print()
    console.rule("[bold green]Your Turn[/bold green]")
    answer = Prompt.ask(f"[bold green]{entrepreneur_name}[/bold green]")
    conversation.append({"role": "Entrepreneur", "content": answer})

    # Round 2: Debate
    console.print()
    console.rule("[bold yellow]🎭  The Debate[/bold yellow]")
    console.print()

    def r2_prompt(judge):
        return build_judge_prompt(
            judge,
            idea_str,
            entrepreneur_name,
            conversation,
            mode,
            2,
            3,
            peer_responses=round1,
        )

    debate = run_judge_round(judges, r2_prompt, label="Debate")
    conversation.extend(
        {"role": r["judge_name"], "content": r["content"]} for r in debate
    )

    # Round 3: Final verdicts
    console.print()
    console.rule("[bold red]🔔  Final Verdicts[/bold red]")
    console.print()

    def r3_prompt(judge):
        return build_judge_prompt(
            judge,
            idea_str,
            entrepreneur_name,
            conversation,
            mode,
            3,
            3,
            peer_responses=debate,
        )

    final = run_judge_round(
        judges, r3_prompt, label="VERDICT", spinner="Panel delivering verdicts…"
    )

    show_verdict_summary(judges, final, idea)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

_RUNNERS = {
    "quick": run_quick_or_rapid,
    "rapid_fire": run_quick_or_rapid,
    "normal": run_normal_or_full_tank,
    "full_tank": run_normal_or_full_tank,
    "panel_debate": run_panel_debate,
}


def main():
    show_welcome()

    demo_mode = Confirm.ask(
        "[bold yellow]⚡  Run in DEMO MODE?[/bold yellow] [dim](autofills SharkLab AI pitch)[/dim]",
        default=False,
    )

    if demo_mode:
        idea = DEMO_IDEA
        selected_judges = [JUDGES[jid] for jid in DEMO_JUDGE_IDS if jid in JUDGES]
        selected_mode = MODES[DEMO_MODE_ID]
        console.print()
        console.print(
            Panel(
                f"[bold cyan]Demo pitch:[/bold cyan] {idea['name']}  ·  "
                f"[bold cyan]Judges:[/bold cyan] {', '.join(j.name for j in selected_judges)}  ·  "
                f"[bold cyan]Mode:[/bold cyan] {selected_mode.name}",
                title="[bold yellow]⚡  Demo Mode[/bold yellow]",
                border_style="yellow",
            )
        )
    else:
        console.rule("[bold cyan]Step 1 — Choose Your Judges[/bold cyan]")
        console.print()
        show_judge_table()
        selected_judges = select_judges()

        console.print()
        console.rule("[bold cyan]Step 2 — Choose a Mode[/bold cyan]")
        console.print()
        show_mode_table()
        selected_mode = select_mode()

        console.print()
        console.rule("[bold cyan]Step 3 — Your Business Idea[/bold cyan]")
        idea = collect_business_idea()

    show_selected_summary(selected_judges, selected_mode)

    if not Confirm.ask("[bold cyan]Ready to pitch?[/bold cyan]", default=True):
        console.print("[dim]Pitch cancelled. Come back when you're ready.[/dim]")
        return

    runner = _RUNNERS.get(selected_mode.id, run_quick_or_rapid)
    runner(selected_judges, selected_mode, idea)

    console.print()
    console.rule("[bold cyan]Session Complete[/bold cyan]")
    console.print(
        "[dim]Run [bold]python demo.py[/bold] again to start a new session.[/dim]\n"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye.[/dim]")
