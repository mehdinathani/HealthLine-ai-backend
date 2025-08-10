# app/my_tools.py

import json
from agents import function_tool
from typing import Optional
import os # <--- ADD THIS LINE



# --- File Paths (This part is correct) ---
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"

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

# --- Tool Functions (These are the ones we need to fix) ---

@function_tool
def find_doctor_by_name(doctor_name: str) -> str:
    """
    Finds schedule entries for a doctor. Returns a JSON string.
    """
    print("Find Doctor tool called")
    schedule = load_schedule()
    # It now calls our simple, internal function
    matching_doctors = _internal_find_doctor(doctor_name, schedule)
    return json.dumps(matching_doctors)


@function_tool
def list_doctors_by_specialty(specialty: str) -> str: # FIXED: Return type is now str
    """
    Finds all doctors within a given specialty.
    Returns the result as a JSON string.
    """
    schedule = load_schedule()
    search_term = specialty.lower()
    matching_specialists = [
        entry for entry in schedule
        if search_term in entry['specialty'].lower()
    ]
    return json.dumps(matching_specialists) # FIXED: Return the list as a JSON string

# --- Helper Functions (Not tools for the agent) ---

def check_availability(doctor_name: str, day: str):
    """
    Internal helper function to check availability.
    """
    print("[TOOL-DEBUG] Inside check_availability...")
    schedule = load_schedule()
    # FIXED: It now calls our simple, internal function. No .func() needed.
    doctor_schedules = _internal_find_doctor(doctor_name, schedule)
    
    if not doctor_schedules:
        print("[TOOL-DEBUG] check_availability: Doctor not found.")
        return None

    print(f"[TOOL-DEBUG] check_availability: Found {len(doctor_schedules)} schedules for this doctor.")
    search_day = day.lower()
    for entry in doctor_schedules:
        if search_day in [d.lower() for d in entry['days']]:
            if "on leave" not in entry.get("time", "").lower():
                print("[TOOL-DEBUG] check_availability: Found available slot.")
                return entry
    
    print("[TOOL-DEBUG] check_availability: No slot matched the requested day.")
    return None


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
@function_tool
def book_appointment(doctor_name: str, day: str, patient_name: str, patient_phone: str) -> str: # <--- FIXED: Return type is str
    """
    Books an appointment if available. Returns a JSON string confirming status.
    """
    print(f"\n[TOOL-DEBUG] --- Starting book_appointment ---")
    print(f"[TOOL-DEBUG] Received: doctor_name='{doctor_name}', day='{day}', patient_name='{patient_name}', patient_phone='{patient_phone}'")

    available_slot = check_availability(doctor_name, day)
    
    if not available_slot:
        print(f"[TOOL-DEBUG] Availability check FAILED for Dr. {doctor_name} on {day}.")
        # FIXED: Return a consistent JSON string
        return json.dumps({
            "success": False, 
            "message": f"Booking failed. Dr. {doctor_name} is not available on {day}."
        })

    print(f"[TOOL-DEBUG] Availability check SUCCEEDED. Slot found: {available_slot}")

    new_booking = {
        "patient_name": patient_name, "patient_phone": patient_phone,
        "doctor_name": available_slot['doctor'], "specialty": available_slot['specialty'],
        "day": day.capitalize(), "time": available_slot['time'], "clinic": available_slot['clinic']
    }

    print(f"[TOOL-DEBUG] Attempting to save booking: {new_booking}")
    try:
        bookings = []
        if os.path.exists(BOOKINGS_FILE):
            with open(BOOKINGS_FILE, 'r') as f:
                content = f.read()
                if content: bookings = json.loads(content)
        
        bookings.append(new_booking)

        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(bookings, f, indent=4)

    except Exception as e:
        print(f"[TOOL-DEBUG] ERROR saving booking: {e}")
        # FIXED: Return a consistent JSON string
        return json.dumps({"success": False, "message": f"A system error occurred while saving the booking."})
    
    print(f"[TOOL-DEBUG] Booking saved successfully.")

    confirmation_message = (
        f"Your appointment with {new_booking['doctor_name']} is confirmed "
        f"for {new_booking['day']} at {new_booking['time']}. Clinic: {new_booking['clinic']}"
    )
    send_sms(patient_phone, confirmation_message)

    print(f"[TOOL-DEBUG] --- Finished book_appointment ---\n")
    # FIXED: Return a consistent JSON string
    return json.dumps({"success": True, "booking": new_booking})

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