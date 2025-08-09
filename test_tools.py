# test_tools.py

import json
from app import tools

def pretty_print(data):
    """Helper function to print data in a readable format."""
    print(json.dumps(data, indent=2))

def run_test_cli():
    """A simple command-line interface to test the tool functions."""
    print("\n--- Hospital Agent Tools Test CLI ---")
    print("Type 'help' for a list of commands, or 'exit' to quit.")

    while True:
        command_str = input("\nEnter command > ").lower().strip()

        if not command_str:
            continue
        
        if command_str == 'exit':
            print("Exiting test CLI.")
            break
        
        if command_str == 'help':
            print("\nAvailable Commands:")
            print("  find <doctor_name>          - Finds a doctor by name.")
            print("  list <specialty>            - Lists doctors by specialty.")
            print("  check <doctor_name> <day>   - Checks availability for a doctor on a day.")
            print("  book <doctor_name> <day> <patient_name> <phone> - Books an appointment.")
            print("  exit                        - Quits the CLI.")
            continue

        parts = command_str.split()
        command = parts[0]
        args = parts[1:]

        try:
            if command == 'find' and len(args) >= 1:
                doctor_name = " ".join(args)
                result = tools.find_doctor_by_name(doctor_name)
                pretty_print(result)

            elif command == 'list' and len(args) >= 1:
                specialty = " ".join(args)
                result = tools.list_doctors_by_specialty(specialty)
                pretty_print(result)

            elif command == 'check' and len(args) >= 2:
                doctor_name = args[0]
                day = args[1]
                result = tools.check_availability(doctor_name, day)
                if result:
                    pretty_print(result)
                else:
                    print(f"No availability found for Dr. {doctor_name.capitalize()} on {day.capitalize()}.")

            elif command == 'book' and len(args) >= 4:
                doctor_name = args[0]
                day = args[1]
                patient_name = args[2] # In a real app, you might need quotes for names with spaces
                phone = args[3]
                result = tools.book_appointment(doctor_name, day, patient_name, phone)
                pretty_print(result)
                
            else:
                print("Invalid command or wrong number of arguments. Type 'help' for details.")
        
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_test_cli()