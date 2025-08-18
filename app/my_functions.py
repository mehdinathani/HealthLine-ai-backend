
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
INFO_FILE = "hospital_info.json"


def get_hospital_info() -> dict:
    """Loads the general hospital information from its JSON file."""
    try:
        with open(INFO_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"error": "Hospital information file not found or is invalid."}

def _internal_find_doctor(doctor_name: str, schedule: list) -> list:
    """
    Upgraded internal function for finding a doctor using word set matching.
    """
    if not doctor_name:
        return []
    
    # Clean and split the search query into a set of words
    search_words = set(doctor_name.lower().replace('dr.', '').replace('dr', '').replace('prof', '').strip().split())
    
    matching_doctors = []
    for entry in schedule:
        doc_name_from_schedule = entry.get('doctor', '')
        if not doc_name_from_schedule:
            continue
        
        # Clean and split the doctor's name from the schedule into a set of words
        schedule_name_words = set(doc_name_from_schedule.lower().replace('dr.', '').replace('dr', '').replace('prof', '').strip().split())
        
        # Check if all search words are present in the doctor's name
        if search_words.issubset(schedule_name_words):
            matching_doctors.append(entry)
            
    # De-duplicate the results based on the doctor's name
    unique_doctors = {doc['doctor']: doc for doc in matching_doctors}.values()
    return list(unique_doctors)

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

# In app/my_functions.py

def _internal_cancel_booking(appointment_id: str) -> bool:
    """
    Finds a booking by its unique appointment_id and removes it.
    Returns True if successful, False otherwise.
    """
    all_bookings = load_bookings()
    
    # Find the booking to remove
    booking_to_remove = None
    for booking in all_bookings:
        if booking.get('appointment_id') == appointment_id:
            booking_to_remove = booking
            break
            
    if not booking_to_remove:
        return False # Booking ID not found

    # Remove the booking and write the file back
    all_bookings.remove(booking_to_remove)
    try:
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(all_bookings, f, indent=4)
        return True # Success
    except Exception as e:
        print(f"Error writing bookings file during cancellation: {e}")
        return False # Failed to write file
    
def load_bookings() -> list:
    """Loads all current bookings from the JSON file."""
    try:
        # We need to reference the file path defined in this file
        with open(BOOKINGS_FILE, 'r') as f:
            # Handle empty file case
            content = f.read()
            if content:
                return json.loads(content)
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    

def get_unique_specialties() -> list:
    """Extracts a unique, sorted list of all specialties from the schedule."""
    schedule = load_schedule()
    all_specialties = {entry.get('specialty', 'N/A') for entry in schedule}
    # Sort and remove any 'N/A' if it exists
    sorted_specialties = sorted([s for s in all_specialties if s != 'N/A'])
    return sorted_specialties