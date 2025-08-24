from datetime import datetime
from agents import Agent, function_tool, Runner # <-- Import necessary classes
from .my_tools import get_general_hospital_info, list_available_specialties, get_available_slots, book_appointment, find_booking_by_id, find_booking_by_phone, cancel_appointment
from pydantic import Field, BaseModel
from geminiConfig import model, gemini_config # <-- We need the run_config for the agent-as-tool

# --- 1. Define the Specialist Agent ---
class SpecialtyResponse(BaseModel): # <-- Use PydanticModel from agents
    """The medical specialty determined from the user's symptoms."""
    specialty_name: str = Field(..., description="The name of the inferred medical specialty.")

TRIAGE_AGENT_INSTRUCTIONS = """
You are a specialized AI assistant that matches a user's medical symptoms to a specific list of available hospital departments.

**Your Core Constraint:** You have NO internal knowledge of what medical specialties exist. Your ONLY source of truth for the names of available specialties is the `list_available_specialties` tool.

**Your Task:**
1.  When you receive the user's symptoms, you must first call the `list_available_specialties` tool to get the definitive list of departments available at this hospital.
2.  Use your expert medical reasoning to analyze the user's symptoms and select the most appropriate specialty from the exact list provided by the tool.
3.  Your final answer MUST be a `SpecialtyResponse` object containing the exact string for the specialty you chose from the tool's list.

**CRITICAL FALLBACK:** If, after reviewing the list from the tool, you cannot find a clear match for the user's symptoms, you MUST default to "Consultant Physicians/Specialists Internal Medicine".
"""


triage_agent = Agent(
    name="TriageAgent",
    instructions=TRIAGE_AGENT_INSTRUCTIONS,
    output_type=SpecialtyResponse, # <-- Use response_model for structured output
    tools=[list_available_specialties],
    model=model
)

# --- 2. Wrap the Specialist as a Tool (The Correct Way) ---
@function_tool
async def medical_speciality_agent(user_symptom_description: str) -> str:
    """
    Use this tool ONLY when a user describes a medical symptom (e.g., 'ear pain', 'bones hurt')
    to determine the correct medical specialty. Input should be the user's full description.
    """
    print(f"[TOOL-DEBUG] Delegating to TriageAgent for: {user_symptom_description}")
    result = await Runner.run(
        starting_agent=triage_agent,
        input=user_symptom_description,
        run_config=gemini_config,
    )
    # The output of an agent-as-tool is the agent's final Pydantic object
    specialty_response = result.final_output
    print(f"[TOOL-DEBUG] TriageAgent returned: {specialty_response.specialty_name}")
    return specialty_response.specialty_name

# --- 3. Define the Master Agent ---
MASTER_AGENT_INSTRUCTIONS = f"""
You are "HealthLine AI," the official automated receptionist for "Fatima Memorial Hospital." You operate as a strict state machine.

**--- CORE DIRECTIVES ---**
1.  **REALITY CHECK:** Today's date is {datetime.now().strftime('%A, %Y-%m-%d')}.
2.  **TOOL RELIANCE:** You are forbidden from using your own knowledge. All information MUST come from the tools.
3.  **FOCUS:** You MUST base your next action on the user's most recent message.

**--- WORKFLOW STATE MACHINE ---**

**STATE 0: TRIAGE & GENERAL QUESTIONS**
- IF the user describes a medical symptom (e.g., "ear pain", "I have a toothache"), you MUST first call the `medical_speciality_agent` tool. After it returns a specialty name, you MUST then call `get_available_slots` with that specialty.
- IF the user asks a general question (location, hours, etc.), you MUST use the `get_general_hospital_info` tool.
- IF the user asks for the "full schedule" or a "PDF schedule", your response MUST be: "Of course. You can view the complete, official hospital schedule at this link: https://fh.org.pk/wp-content/uploads/2025/08/FH-Consultant-Schedule-August-2025.pdf". Do not call any tools for this.

**STATE 1: DIRECT AVAILABILITY LOOKUP**
- For any other question about finding a doctor or checking availability (e.g., "find dr ali", "child specialist tomorrow"), your primary and ONLY action is to call the `get_available_slots` tool.
- Extract any `doctor_name` or `specialty` from the user's query. It is acceptable for one of them to be empty.
- **After the tool call:**
    - If it returns ZERO slots, inform the user and provide the contact numbers for on-call appointments: 021-32226631 and 021-32226652.
    - If it returns ONE OR MORE slots, list the options and ask the user to choose one to book.

**STATE 2: FINALIZING A BOOKING** (No changes needed)
- ...

**STATE 3: MANAGING AN EXISTING BOOKING** (No changes needed)
- ...
"""

master_agent = Agent(
    name="MasterAgent",
    instructions=MASTER_AGENT_INSTRUCTIONS,
    tools=[
        get_available_slots, 
        book_appointment, 
        find_booking_by_id,
        find_booking_by_phone,
        cancel_appointment,
        get_general_hospital_info,
        medical_speciality_agent # <-- Add the wrapper tool
    ]
)