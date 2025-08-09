# main.py

import asyncio
from agents import Runner, set_tracing_disabled
from geminiConfig import gemini_config
from app.my_agents import master_agent # Corrected import path

# Disabling tracing for a cleaner console output
set_tracing_disabled(True)

async def main():
    print("--- HealthLine AI Assistant ---")
    print("Ask about doctor schedules or book an appointment. Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\nYou > ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting. Thank you for using HealthLine!")
                break
            
            if not user_input:
                continue

            print("\nAssistant is thinking...")
            
            # Run the agent with the user's input
            result = await Runner.run(
                starting_agent=master_agent,
                input=user_input,
                run_config=gemini_config,
            )

            # Print the final output from the agent
            print(f"\nAssistant > {result.final_output}")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    asyncio.run(main())