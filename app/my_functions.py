
import json
from typing import Optional
import os # <--- ADD THIS LINE
from datetime import datetime, timedelta



# --- File Paths (This part is correct) ---
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"
ABSENTS_FILE = "dr_absents.json"

# --- Helper Function (This part is correct) ---
def load_schedule():
    print("Load Schedule tool called")
    """Loads the full hospital schedule from the JSON file."""
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The schedule file was not found at {SCHEDULE_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"Error: The schedule file at {SCHEDULE_FILE} is not a valid JSON.")
        return []

# --- Helper Functions (Not tools for the agent) ---

# def check_availability(doctor_name: str, day: str):
#     """
#     Internal helper function to check availability.
#     """
#     print("[TOOL-DEBUG] Inside check_availability...")
#     schedule = load_schedule()
#     # FIXED: It now calls our simple, internal function. No .func() needed.
#     doctor_schedules = _internal_find_doctor(doctor_name, schedule)
    
#     if not doctor_schedules:
#         print("[TOOL-DEBUG] check_availability: Doctor not found.")
#         return None

#     print(f"[TOOL-DEBUG] check_availability: Found {len(doctor_schedules)} schedules for this doctor.")
#     search_day = day.lower()
#     for entry in doctor_schedules:
#         if search_day in [d.lower() for d in entry['days']]:
#             if "on leave" not in entry.get("time", "").lower():
#                 print("[TOOL-DEBUG] check_availability: Found available slot.")
#                 return entry
    
#     print("[TOOL-DEBUG] check_availability: No slot matched the requested day.")
#     return None


def send_sms(phone: str, message: str):
    """Simulates sending an SMS by printing the message to the console."""
    print(f"[SMS to {phone}] {message}")

# in app/tools.py

# (Make sure these imports are at the top of your tools.py file)
import json
from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"

def _internal_find_doctor(doctor_name: str, schedule: list) -> list:
    """
    Internal-only function for finding a doctor. Not a tool for the agent.
    This contains the robust search logic.
    """
    if not doctor_name:
        return []
    
    search_term = doctor_name.lower().replace('dr.', '').replace('dr', '').replace('prof', '').strip()
    
    matching_doctors = []
    for entry in schedule:
        schedule_doc_name = entry['doctor'].lower().replace('dr.', '').replace('dr', '').replace('prof', '').strip()
        if search_term in schedule_doc_name:
            matching_doctors.append(entry)
            
    return matching_doctors

# (add this function near your other load functions)

def load_absences() -> dict:
    """Loads the doctor absences from the JSON file."""
    try:
        if os.path.exists(ABSENTS_FILE):
            with open(ABSENTS_FILE, 'r') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file is missing or invalid, assume no one is absent.
        return {}
    return {}