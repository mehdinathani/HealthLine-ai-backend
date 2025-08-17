# app/my_tools.py

import json
from agents import function_tool
from typing import Optional
import os
from datetime import datetime, timedelta
import uuid
from .my_functions import get_hospital_info, load_bookings, load_schedule, load_absences, _internal_find_doctor, send_sms, _internal_cancel_booking

# --- File Paths ---
SCHEDULE_FILE = "full_hospital_schedule_with_specialty.json"
BOOKINGS_FILE = "bookings.json"
ABSENTS_FILE = "dr_absents.json"


@function_tool
def get_available_slots(
    doctor_name: str = None, 
    specialty: str = None
) -> str:
    """
    Calculates ALL available appointment slots for the next 14 days,
    optionally filtered by a doctor's name or a specialty.
    """
    print(f"[TOOL-DEBUG] Final search for: Dr={doctor_name}, Spec={specialty}")
    
    try:
        candidate_schedules = load_schedule()

        if specialty:
            candidate_schedules = [s for s in candidate_schedules if specialty.lower() in s.get('specialty', '').lower()]
        
        if doctor_name:
            candidate_schedules = _internal_find_doctor(doctor_name, candidate_schedules)

        if not candidate_schedules:
            return json.dumps({"success": True, "slots": []})

        absences = load_absences()
        all_bookings = load_bookings()

        available_slots = []
        today = datetime.now()
        for i in range(14):
            check_date = today + timedelta(days=i)
            check_date_str = check_date.strftime("%Y-%m-%d")
            current_day_of_week = check_date.strftime("%A")

            for schedule_entry in candidate_schedules:
                if "on leave" in schedule_entry.get('time', '').lower():
                    continue

                doc_full_name = schedule_entry.get('doctor')
                if not doc_full_name:
                    continue

                if current_day_of_week in schedule_entry.get('days', []):
                    doctor_absent_dates = absences.get(doc_full_name, [])
                    if check_date_str in doctor_absent_dates:
                        continue
                    
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

    except Exception as e:
        print(f"[TOOL-ERROR] get_available_slots failed: {e}")
        return json.dumps({"success": False, "message": f"An internal system error occurred: {str(e)}"})
    

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
def list_doctors_by_specialty(specialty: str) -> str:
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
    return json.dumps(matching_specialists)


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


@function_tool
def find_booking_by_phone(phone_number: str) -> str:
    """
    Finds existing bookings using ONLY the patient's phone number.
    """
    print(f"[TOOL-DEBUG] Finding bookings for phone: {phone_number}")
    all_bookings = load_bookings()
    found_bookings = [b for b in all_bookings if b.get('patient_phone') == phone_number]
    return json.dumps({"success": True, "bookings": found_bookings})

@function_tool
def find_booking_by_id(appointment_id: str) -> str:
    """
    Finds an existing booking using ONLY the unique appointment ID.
    """
    print(f"[TOOL-DEBUG] Finding booking for ID: {appointment_id}")
    all_bookings = load_bookings()
    found_bookings = [b for b in all_bookings if b.get('appointment_id') == appointment_id]
    return json.dumps({"success": True, "bookings": found_bookings})


@function_tool
def cancel_appointment(appointment_id: str) -> str:
    """
    Cancels an appointment using its unique appointment_id.
    """
    print(f"[TOOL-DEBUG] Attempting to cancel appointment ID: {appointment_id}")
    
    success = _internal_cancel_booking(appointment_id)
    
    if success:
        return json.dumps({"success": True, "message": f"Successfully cancelled appointment {appointment_id}."})
    else:
        return json.dumps({"success": False, "message": f"Failed to cancel appointment {appointment_id}. The ID may not exist."})

@function_tool
def get_general_hospital_info(question: str) -> str:
    """
    Used to answer general questions about the hospital, such as location,
    contact details, visiting hours, parking, or available departments.
    The 'question' parameter should be the user's original query.
    """
    print(f"[TOOL-DEBUG] Getting general info for question: {question}")
    
    # This tool's job is simple: retrieve ALL the information.
    # The AI model will then intelligently find the answer within this data.
    info_data = get_hospital_info()
    
    # Return the entire info blob as a JSON string.
    return json.dumps(info_data)