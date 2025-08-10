# app/my_tools.py

import json
from agents import function_tool
from typing import Optional
import os # <--- ADD THIS LINE
from datetime import datetime, timedelta
import uuid # <--- ADD THIS FINAL IMPORT
from .my_functions import load_schedule, load_absences, _internal_find_doctor,send_sms



# --- File Paths (This part is correct) ---
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"
ABSENTS_FILE = "dr_absents.json"


@function_tool
def get_available_slots(doctor_name: str) -> str:
    """
    Calculates the true, available appointment slots for a specific doctor
    for the next 14 days, considering their schedule, absences, and existing bookings.
    Only 20 appointments per doctor per day are allowed.
    """
    print(f"[TOOL-DEBUG] Getting available slots for: {doctor_name}")
    
    # 1. Load all necessary data
    schedule = load_schedule()
    absences = load_absences()
    try:
        with open(BOOKINGS_FILE, 'r') as f:
            all_bookings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_bookings = []

    # 2. Find the specific doctor's base schedule
    doctor_schedules = _internal_find_doctor(doctor_name, schedule)
    if not doctor_schedules:
        return json.dumps({"success": False, "message": "Doctor not found."})

    # 3. Get doctor's specific absences
    doctor_absent_dates = absences.get(doctor_schedules[0]['doctor'], [])

    # 4. Generate the next 14 days and check each one
    available_slots = []
    today = datetime.now()
    
    for i in range(14): # Check for the next 14 days
        check_date = today + timedelta(days=i)
        check_date_str = check_date.strftime("%Y-%m-%d") # Format: "2025-08-20"
        day_of_week = check_date.strftime("%A") # Format: "Tuesday"

        # Is the doctor absent on this specific date?
        if check_date_str in doctor_absent_dates:
            continue # Skip to the next day

        # Does the doctor work on this day of the week?
        for schedule_entry in doctor_schedules:
            if day_of_week in schedule_entry['days']:
                # Count existing bookings for this doctor on this date
                bookings_on_date = [
                    b for b in all_bookings 
                    if b.get('doctor_name') == schedule_entry['doctor'] and b.get('booking_date') == check_date_str
                ]
                
                # Check if the slot is full (as per the 20 patient policy)
                if len(bookings_on_date) < 20:
                    available_slots.append({
                        "date": check_date_str,
                        "day": day_of_week,
                        "time": schedule_entry['time'],
                        "clinic": schedule_entry['clinic'],
                        "available_spots": 20 - len(bookings_on_date)
                    })

    return json.dumps({"success": True, "slots": available_slots})

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



import json

# BASE_DIR = Path(__file__).resolve().parent.parent
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"
@function_tool
def book_appointment(doctor_name: str, booking_date: str, booking_time: str, patient_name: str, patient_phone: str) -> str:
    """
    Finalizes and saves a patient's appointment. This is the final, robust version.
    """
    print(f"\n[TOOL-DEBUG] --- Starting Final Booking ---")
    print(f"[TOOL-DEBUG] Received: Dr={doctor_name}, Date={booking_date}, Time={booking_time}, Patient={patient_name}, Phone={patient_phone}")

    # 1. Load existing bookings
    try:
        with open(BOOKINGS_FILE, 'r') as f:
            all_bookings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_bookings = []

    # 2. Calculate the next token number using .get() for safety
    bookings_today = [
        b for b in all_bookings 
        if b.get('doctor_name') == doctor_name and b.get('booking_date') == booking_date
    ]
    token_number = len(bookings_today) + 1

    if token_number > 20:
        return json.dumps({"success": False, "message": "Sorry, the clinic is fully booked for this doctor on this day."})
    
    # 3. Find doctor's details from the main schedule
    schedule = load_schedule()
    doctor_info_list = _internal_find_doctor(doctor_name, schedule)
    
    if not doctor_info_list:
         return json.dumps({"success": False, "message": "Critical error: Could not find the doctor's base schedule information."})

    # --- THIS IS THE KEY RESILIENCY FIX ---
    # We safely get the first schedule entry and use .get() for resilience against bad data.
    doctor_schedule_entry = doctor_info_list[0]
    specialty = doctor_schedule_entry.get('specialty', 'N/A')
    clinic = doctor_schedule_entry.get('clinic', 'N/A')

    # 4. Generate the new booking record
    new_booking = {
        "appointment_id": str(uuid.uuid4()),
        "token_number": token_number,
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "doctor_name": doctor_name,
        "specialty": specialty,
        "booking_date": booking_date,
        "booking_time": booking_time,
        "clinic": clinic
    }

    print(f"[TOOL-DEBUG] Attempting to save booking: {new_booking}")
    try:
        all_bookings.append(new_booking)
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(all_bookings, f, indent=4)
    except Exception as e:
        print(f"[TOOL-DEBUG] ERROR saving booking: {e}")
        return json.dumps({"success": False, "message": f"A system error occurred while saving the booking. Details: {str(e)}"})

    print(f"[TOOL-DEBUG] Booking saved successfully.")

    # 5. Simulate SMS Confirmation
    confirmation_message = (
        f"Appointment Confirmed! Your appointment with {doctor_name} is on "
        f"{booking_date} at {booking_time}. Your token number is {token_number}. "
        f"Please arrive at clinic {clinic}."
    )
    send_sms(patient_phone, confirmation_message)

    return json.dumps({"success": True, "booking": new_booking})


