# app/my_tools.py

import json
from agents import function_tool
from typing import Optional


# --- File Paths (This part is correct) ---
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"

# --- Helper Function (This part is correct) ---
def load_schedule() -> list[dict]:
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
def find_doctor_by_name(doctor_name: str) -> str: # FIXED: Return type is now str
    print("Find Doctor tool called")
    """
    Finds all schedule entries for a doctor by their name, allowing for partial matches.
    Returns the result as a JSON string.
    """
    schedule = load_schedule()
    if not doctor_name:
        return json.dumps([]) # FIXED: Return an empty JSON list as a string
    
    search_term = doctor_name.lower()
    matching_doctors = [
        entry for entry in schedule
        if search_term in entry['doctor'].lower()
    ]
    return json.dumps(matching_doctors) # FIXED: Use json.dumps to return a string

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

def check_availability(doctor_name: str, day: str) -> Optional[dict]:
    """
    Internal helper function to check availability. Not a tool for the agent.
    """
    # FIXED: This is a critical change. Since find_doctor_by_name now returns a string,
    # we must call its underlying function with .func() and then parse the JSON string.
    schedules_str = find_doctor_by_name.func(doctor_name=doctor_name)
    doctor_schedules = json.loads(schedules_str)
    
    if not doctor_schedules:
        return None

    search_day = day.lower()
    for entry in doctor_schedules:
        if search_day in [d.lower() for d in entry['days']]:
            if "on leave" not in entry.get("time", "").lower():
                return entry
    
    return None

def send_sms(phone: str, message: str):
    """Simulates sending an SMS by printing the message to the console."""
    print(f"[SMS to {phone}] {message}")

@function_tool
def book_appointment(doctor_name: str, day: str, patient_name: str, patient_phone: str) -> str: # FIXED: Return type is now str
    """
    Books an appointment if the slot is available and saves it to a file.
    Returns a confirmation or error message as a JSON string.
    """
    available_slot = check_availability(doctor_name, day)
    
    if not available_slot:
        result = {"success": False, "message": f"Dr. {doctor_name} is not available on {day}."}
        return json.dumps(result) # FIXED: Return the dict as a JSON string

    new_booking = {
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "doctor_name": available_slot['doctor'],
        "specialty": available_slot['specialty'],
        "day": day.capitalize(),
        "time": available_slot['time'],
        "clinic": available_slot['clinic']
    }

    try:
        with open(BOOKINGS_FILE, 'r+') as f:
            bookings = json.load(f)
            bookings.append(new_booking)
            f.seek(0)
            json.dump(bookings, f, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump([new_booking], f, indent=4)
    
    confirmation_message = (
        f"Your appointment with {new_booking['doctor_name']} is confirmed "
        f"for {new_booking['day']} at {new_booking['time']}. "
        f"Clinic: {new_booking['clinic']}"
    )
    send_sms(patient_phone, confirmation_message)

    result = {"success": True, "booking": new_booking}
    return json.dumps(result) # FIXED: Return the success dict as a JSON string