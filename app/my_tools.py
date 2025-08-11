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
def get_available_slots(
    doctor_name: str = None, 
    specialty: str = None, 
    day_of_week: str = None
) -> str:
    """
    Calculates available appointment slots based on a flexible search.
    Can filter by doctor name, specialty, and/or a specific day of the week for the next 14 days.
    """
    # The rest of the function body is PERFECT and does not need to change.
    print(f"[TOOL-DEBUG] Advanced search for: Dr={doctor_name}, Spec={specialty}, Day={day_of_week}")
    
    # 1. Start with the full schedule and apply filters
    candidate_schedules = load_schedule()

    if specialty:
        candidate_schedules = [s for s in candidate_schedules if specialty.lower() in s.get('specialty', '').lower()]
    
    if doctor_name:
        candidate_schedules = _internal_find_doctor(doctor_name, candidate_schedules)

    if not candidate_schedules:
        return json.dumps({"success": True, "slots": []})

    # 2. Load absences and all current bookings
    absences = load_absences()
    try:
        with open(BOOKINGS_FILE, 'r') as f: all_bookings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): all_bookings = []

    # 3. Check availability over the next 14 days
    available_slots = []
    today = datetime.now()
    for i in range(14):
        check_date = today + timedelta(days=i)
        check_date_str = check_date.strftime("%Y-%m-%d")
        current_day_of_week = check_date.strftime("%A")

        if day_of_week and day_of_week.lower() not in current_day_of_week.lower():
            continue

        for schedule_entry in candidate_schedules:
            doc_full_name = schedule_entry.get('doctor', '')
            if not doc_full_name: continue

            doctor_absent_dates = absences.get(doc_full_name, [])
            if check_date_str in doctor_absent_dates:
                continue

            if "on leave" in schedule_entry.get('time', '').lower():
                continue # Skip this slot entirely if the doctor is on leave
            # --- END OF ADDED BLOCK ---

            if current_day_of_week in schedule_entry.get('days', []):
                bookings_on_date = [b for b in all_bookings if b.get('doctor_name') == doc_full_name and b.get('booking_date') == check_date_str]
                if len(bookings_on_date) < 20:
                    available_slots.append({
                        "doctor": doc_full_name,
                        "date": check_date_str,
                        "day": current_day_of_week,
                        "time": schedule_entry.get('time', 'N/A'),
                        "clinic": schedule_entry.get('clinic', 'N/A'),
                    })
    
    return json.dumps({"success": True, "slots": available_slots})


@function_tool
def find_doctor_by_name(doctor_name: str) -> str:
    """
    Finds doctors by name and returns a simplified list of their names and specialties.
    """
    print("Find Doctor tool called")
    schedule = load_schedule()
    matching_doctors = _internal_find_doctor(doctor_name, schedule)

    # --- THIS IS THE KEY CHANGE ---
    # Instead of returning everything, create a clean, simple list.
    simplified_results = [
        {
            "doctor": doc.get('doctor', 'N/A'),
            "specialty": doc.get('specialty', 'N/A')
        } 
        for doc in matching_doctors
    ]
    
    return json.dumps(simplified_results)

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
        f"Appointment Confirmed! Appt ID: {new_booking['appointment_id']}. "  # <-- ADDED Appt ID
        f"Your appointment with {doctor_name} is on "
        f"{booking_date} at {booking_time}. Your token number is {token_number}. "
        f"Please arrive at clinic {clinic}."
    )
    send_sms(patient_phone, confirmation_message)

    return json.dumps({
        "success": True, 
        "booking": new_booking,
        "message": f"The booking is confirmed. The appointment ID is {new_booking['appointment_id']} and the token number is {token_number}." # <-- New helpful message
    })


