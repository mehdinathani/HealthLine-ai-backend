from datetime import datetime
from agents import Agent
from pydantic import Field, BaseModel
from geminiConfig import model, gemini_config

# --- Import ALL necessary tools for all agents ---
from .my_tools import (
    find_slots_by_doctor_name,
    find_slots_by_specialty,
    book_appointment,
    find_booking_by_id,
    find_booking_by_phone,
    cancel_appointment,
    get_general_hospital_info,
    list_available_specialties
)

# === SPECIALIST AGENT DEFINITIONS ===

# --- AGENT 1: Symptom Analysis Expert ---
class InferredSpecialty(BaseModel):
    inferred_specialty: str = Field(..., description="The general medical term for the specialty, e.g., 'Otolaryngology'.")

SYMPTOM_AGENT_INSTRUCTIONS = "You are a medical expert. Analyze the user's symptoms and return the technically correct, general medical specialty using the `InferredSpecialty` model."

symptom_analysis_agent = Agent(
    name="SymptomAnalysisAgent",
    instructions=SYMPTOM_AGENT_INSTRUCTIONS,
    output_type=InferredSpecialty,
    tools=[],
    model=model
)

# --- AGENT 2: Data Matching Expert ---
class MatchedSpecialty(BaseModel):
    matched_specialty: str = Field(..., description="The exact specialty string from the provided list that best matches the target.")

MATCHER_AGENT_INSTRUCTIONS = "You are a data matching AI. You are given a 'target_specialty' and a 'list_of_available_specialties'. Your ONLY job is to find the single best match for the target from the available list and respond with the `MatchedSpecialty` model. If no good match is found, return 'None'."

specialty_matcher_agent = Agent(
    name="SpecialtyMatcherAgent",
    instructions=MATCHER_AGENT_INSTRUCTIONS,
    output_type=MatchedSpecialty,
    tools=[],
    model=model
)

# --- WRAP THE SPECIALISTS AS TOOLS ---
symptom_tool = symptom_analysis_agent.as_tool(
    tool_name="analyze_symptoms",
    tool_description="Use this agent to analyze a user's medical symptoms to determine the general medical specialty."
)

matcher_tool = specialty_matcher_agent.as_tool(
    tool_name="match_specialty_to_hospital_list",
    tool_description="Use this agent to find the best matching specialty name from the hospital's official list. The input must contain the target specialty and the list to check."
)

# === MASTER AGENT DEFINITION ===
MASTER_AGENT_INSTRUCTIONS = f"""
You are "HealthLine AI," the orchestrator agent for Fatima Hospital. Your job is to manage the conversation and delegate tasks to your tools according to a strict workflow.

**--- CORE DIRECTIVES ---**
1.  **REALITY CHECK:** Today's date is {datetime.now().strftime('%A, %Y-%m-%d')}.
2.  **TOOL RELIANCE:** You are forbidden from answering from your own knowledge. You MUST use tools.

**--- WORKFLOW STATE MACHINE ---**

**STATE 0: TRIAGE WORKFLOW (When a user describes a symptom)**
This is a mandatory, multi-step process. You MUST follow these steps in order:
    a. **Step 1: Analyze.** Call the `analyze_symptoms` tool with the user's symptom description.
    b. **Step 2: Retrieve List.** Call the `list_available_specialties` tool to get the hospital's official list.
    c. **Step 3: Match.** Call the `match_specialty_to_hospital_list` tool. The input MUST include the general specialty from Step 1 AND the official list from Step 2.
    d. **Step 4: Find Availability.** Use the final, correct specialty name returned by the matcher tool to call `find_slots_by_specialty`.

**STATE 1: DIRECT LOOKUP WORKFLOW**
- **IF** the user asks to find a doctor by name (e.g., "find dr mehdi"), you **MUST** use the `find_slots_by_doctor_name` tool.
- **IF** the user asks to find a specialty directly (e.g., "any cardiologists?", "neuro"), you **MUST** perform this sub-routine:
    i. First, call `list_available_specialties` to get the official list.
    ii. Second, call `match_specialty_to_hospital_list` with the user's term and the official list.
    iii. Finally, call `find_slots_by_specialty` with the clean name returned by the matcher tool.
- **IF** a search for slots returns nothing, inform the user and provide the contact number for help: 021-32226631.
- **IF** you find slots, list them and ask the user to choose.

**STATE 2 & 3: BOOKING & CANCELLATION** (These are stable)
- Follow your existing instructions for finalizing a booking and managing existing bookings.
"""

master_agent = Agent(
    name="MasterAgent",
    instructions=MASTER_AGENT_INSTRUCTIONS,
    tools=[
        # The two new, unambiguous search tools
        find_slots_by_doctor_name,
        find_slots_by_specialty,
        
        # Core functionality tools
        book_appointment,
        find_booking_by_id,
        find_booking_by_phone,
        cancel_appointment,
        get_general_hospital_info,
        list_available_specialties,
        
        # Agent-as-Tools
        symptom_tool,
        matcher_tool
    ]
)