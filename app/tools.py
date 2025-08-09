# app/tools.py

import json
from pathlib import Path
import os

# Define the base directory of the project
# This makes our file paths work, no matter where we run the script from
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define paths to our data files using this root
SCHEDULE_FILE = PROJECT_ROOT / "data" / "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = PROJECT_ROOT / "data" / "bookings.json"


def load_schedule() -> list[dict]:
    """
    Loads the full hospital schedule from the JSON file.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary
                    represents a doctor's schedule entry.
    """
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The schedule file was not found at {SCHEDULE_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"Error: The schedule file at {SCHEDULE_FILE} is not a valid JSON.")
        return []

def find_doctor_by_name(doctor_name: str) -> list[dict]:
    """
    Finds all schedule entries for a doctor by their name, allowing for partial matches.

    Args:
        doctor_name (str): The partial or full name of the doctor to search for.

    Returns:
        list[dict]: A list of matching schedule entries. Returns an empty list if no match is found.
    """
    schedule = load_schedule()
    if not doctor_name:
        return []
        
    # Case-insensitive search
    search_term = doctor_name.lower()
    
    matching_doctors = [
        entry for entry in schedule
        if search_term in entry['doctor'].lower()
    ]
    return matching_doctors

# Add this to app/tools.py

def list_doctors_by_specialty(specialty: str) -> list[dict]:
    """
    Finds all doctors within a given specialty.

    Args:
        specialty (str): The specialty to search for (e.g., "Cardiologist").

    Returns:
        list[dict]: A list of schedule entries for all doctors in that specialty.
    """
    schedule = load_schedule()
    search_term = specialty.lower()
    
    matching_specialists = [
        entry for entry in schedule
        if search_term in entry['specialty'].lower()
    ]
    return matching_specialists


# Add this to app/tools.py

def check_availability(doctor_name: str, day: str) -> dict | None:
    """
    Checks if a specific doctor is available on a specific day.

    Args:
        doctor_name (str): The name of the doctor.
        day (str): The day of the week (e.g., "Monday").

    Returns:
        dict | None: The schedule entry if the doctor is available, otherwise None.
    """
    doctor_schedules = find_doctor_by_name(doctor_name)
    if not doctor_schedules:
        return None

    search_day = day.lower()
    for entry in doctor_schedules:
        # Check if the requested day is in the list of available days for that slot
        if search_day in [d.lower() for d in entry['days']]:
            # Also check they are not on leave
            if "on leave" not in entry.get("time", "").lower():
                return entry  # Return the specific available slot
    
    return None # Return None if no slot matches the day


# Add these two functions to app/tools.py

def send_sms(phone: str, message: str):
    """
    Simulates sending an SMS by printing the message to the console.

    Args:
        phone (str): The phone number to send the SMS to.
        message (str): The content of the message.
    """
    print(f"[SMS to {phone}] {message}")


def book_appointment(doctor_name: str, day: str, patient_name: str, patient_phone: str) -> dict:
    """
    Books an appointment if the slot is available and saves it to a file.

    Args:
        doctor_name (str): The name of the doctor.
        day (str): The requested day.
        patient_name (str): The patient's name.
        patient_phone (str): The patient's phone number.

    Returns:
        dict: A dictionary confirming the booking status and details.
    """
    available_slot = check_availability(doctor_name, day)
    
    if not available_slot:
        return {"success": False, "message": f"Dr. {doctor_name} is not available on {day}."}

    # Create the new booking record
    new_booking = {
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "doctor_name": available_slot['doctor'],
        "specialty": available_slot['specialty'],
        "day": day.capitalize(),
        "time": available_slot['time'],
        "clinic": available_slot['clinic']
    }

    # Load existing bookings, add the new one, and save back to the file
    try:
        with open(BOOKINGS_FILE, 'r+') as f:
            bookings = json.load(f)
            bookings.append(new_booking)
            f.seek(0) # Rewind file to the beginning
            json.dump(bookings, f, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty, create it with the new booking
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump([new_booking], f, indent=4)
    
    # Simulate sending a confirmation SMS
    confirmation_message = (
        f"Your appointment with {new_booking['doctor_name']} is confirmed "
        f"for {new_booking['day']} at {new_booking['time']}. "
        f"Clinic: {new_booking['clinic']}"
    )
    send_sms(patient_phone, confirmation_message)

    return {"success": True, "booking": new_booking}